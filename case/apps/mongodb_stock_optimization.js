/**
 * MongoDB股票技术指标计算优化方案
 * 针对MA、RSI等需要历史数据的计算场景
 */

const { MongoClient } = require('mongodb');

class StockIndicatorOptimizer {
    constructor(uri, dbName) {
        this.client = new MongoClient(uri);
        this.db = this.client.db(dbName);
    }

    async connect() {
        await this.client.connect();
        console.log('Connected to MongoDB');
    }

    async disconnect() {
        await this.client.close();
        console.log('Disconnected from MongoDB');
    }

    /**
     * 方案1: 优化的分页查询
     * 只查询必要字段，使用索引，分批获取数据
     */
    async getStockDataOptimized(symbol, requiredDays, startDate = null) {
        const query = { symbol };
        if (startDate) {
            query.date = { $lte: startDate };
        }

        // 只查询必要字段
        const projection = {
            date: 1,
            close: 1,
            high: 1,
            low: 1,
            volume: 1
        };

        const data = await this.db.collection('stocks')
            .find(query)
            .project(projection)
            .sort({ date: -1 })
            .limit(requiredDays)
            .toArray();

        // 按日期正序排列（从旧到新）
        return data.reverse();
    }

    /**
     * 方案2: 使用聚合管道计算技术指标
     * 在数据库层面完成部分计算，减少数据传输
     */
    async calculateIndicatorsWithAggregation(symbol, requiredDays) {
        const pipeline = [
            { $match: { symbol } },
            { $sort: { date: -1 } },
            { $limit: requiredDays },
            { $sort: { date: 1 } }, // 重新排序为正序
            {
                $group: {
                    _id: null,
                    dates: { $push: '$date' },
                    closes: { $push: '$close' },
                    highs: { $push: '$high' },
                    lows: { $push: '$low' }
                }
            }
        ];

        const result = await this.db.collection('stocks')
            .aggregate(pipeline)
            .toArray();

        if (result.length === 0) return null;

        const { dates, closes, highs, lows } = result[0];

        // 计算各种技术指标
        return {
            symbol,
            data: dates.map((date, i) => ({
                date,
                close: closes[i],
                ma5: this.calculateMAFromArray(closes, i, 5),
                ma10: this.calculateMAFromArray(closes, i, 10),
                ma20: this.calculateMAFromArray(closes, i, 20),
                rsi14: this.calculateRSIFromArray(closes, i, 14)
            }))
        };
    }

    /**
     * 方案3: 预计算并存储技术指标
     * 创建专门的指标集合，定期更新
     */
    async preCalculateAndStoreIndicators(symbol) {
        // 获取完整历史数据
        const historicalData = await this.db.collection('stocks')
            .find({ symbol })
            .sort({ date: 1 })
            .toArray();

        if (historicalData.length === 0) return;

        const closes = historicalData.map(d => d.close);
        const indicators = [];

        // 为每一天计算指标
        for (let i = 0; i < historicalData.length; i++) {
            const day = historicalData[i];
            indicators.push({
                symbol,
                date: day.date,
                close: day.close,
                ma5: this.calculateMAFromArray(closes, i, 5),
                ma10: this.calculateMAFromArray(closes, i, 10),
                ma20: this.calculateMAFromArray(closes, i, 20),
                rsi14: this.calculateRSIFromArray(closes, i, 14),
                updatedAt: new Date()
            });
        }

        // 批量插入或更新指标集合
        const bulkOps = indicators.map(indicator => ({
            updateOne: {
                filter: { symbol: indicator.symbol, date: indicator.date },
                update: { $set: indicator },
                upsert: true
            }
        }));

        await this.db.collection('stock_indicators')
            .bulkWrite(bulkOps);

        console.log(`Pre-calculated indicators for ${symbol}`);
    }

    /**
     * 从预计算的指标集合中查询
     */
    async getPreCalculatedIndicators(symbol, requiredDays, endDate = null) {
        const query = { symbol };
        if (endDate) {
            query.date = { $lte: endDate };
        }

        const indicators = await this.db.collection('stock_indicators')
            .find(query)
            .sort({ date: -1 })
            .limit(requiredDays)
            .toArray();

        return indicators.reverse();
    }

    /**
     * 方案4: 使用时间序列集合（MongoDB 5.0+）
     */
    async createTimeSeriesCollection() {
        try {
            await this.db.createCollection('stock_timeseries', {
                timeseries: {
                    timeField: 'date',
                    metaField: 'symbol',
                    granularity: 'days'
                }
            });
            console.log('Time series collection created');
        } catch (error) {
            console.log('Time series collection might already exist');
        }

        // 创建索引
        await this.db.collection('stock_timeseries').createIndex(
            { symbol: 1, date: -1 }
        );
    }

    /**
     * 辅助函数：从数组中计算移动平均
     */
    calculateMAFromArray(closes, index, period) {
        if (index < period - 1) return null;
        
        let sum = 0;
        for (let i = index - period + 1; i <= index; i++) {
            sum += closes[i];
        }
        return sum / period;
    }

    /**
     * 辅助函数：从数组中计算RSI
     */
    calculateRSIFromArray(closes, index, period) {
        if (index < period) return null;

        let gains = 0;
        let losses = 0;

        // 计算初始平均收益和损失
        for (let i = index - period + 1; i <= index; i++) {
            const change = closes[i] - closes[i - 1];
            if (change > 0) {
                gains += change;
            } else {
                losses += Math.abs(change);
            }
        }

        const avgGain = gains / period;
        const avgLoss = losses / period;

        if (avgLoss === 0) return 100;

        const rs = avgGain / avgLoss;
        return 100 - (100 / (1 + rs));
    }

    /**
     * 创建必要的索引
     */
    async createIndexes() {
        // 为stocks集合创建索引
        await this.db.collection('stocks').createIndex(
            { symbol: 1, date: -1 },
            { background: true }
        );

        // 为stock_indicators集合创建索引
        await this.db.collection('stock_indicators').createIndex(
            { symbol: 1, date: -1 },
            { background: true }
        );

        // 创建复合索引用于常用查询
        await this.db.collection('stock_indicators').createIndex(
            { symbol: 1, date: -1, indicator: 1 },
            { background: true }
        );

        console.log('Indexes created successfully');
    }

    /**
     * 批量预计算所有股票的指标
     */
    async batchPreCalculateAllStocks() {
        const symbols = await this.db.collection('stocks')
            .distinct('symbol');

        console.log(`Found ${symbols.length} symbols to process`);

        for (const symbol of symbols) {
            try {
                await this.preCalculateAndStoreIndicators(symbol);
            } catch (error) {
                console.error(`Error processing ${symbol}:`, error.message);
            }
        }

        console.log('Batch pre-calculation completed');
    }
}

// 使用示例
async function main() {
    const optimizer = new StockIndicatorOptimizer(
        'mongodb://localhost:27017',
        'stock_database'
    );

    try {
        await optimizer.connect();
        
        // 创建索引
        await optimizer.createIndexes();
        
        // 方案1: 优化的查询
        console.log('\n=== 方案1: 优化查询 ===');
        const stockData = await optimizer.getStockDataOptimized('AAPL', 100);
        console.log(`Retrieved ${stockData.length} records for AAPL`);
        
        // 方案2: 聚合管道计算
        console.log('\n=== 方案2: 聚合管道 ===');
        const indicators = await optimizer.calculateIndicatorsWithAggregation('AAPL', 100);
        console.log(`Calculated indicators for ${indicators.data.length} days`);
        
        // 方案3: 预计算指标
        console.log('\n=== 方案3: 预计算指标 ===');
        await optimizer.preCalculateAndStoreIndicators('AAPL');
        
        const preCalculated = await optimizer.getPreCalculatedIndicators('AAPL', 50);
        console.log(`Retrieved ${preCalculated.length} pre-calculated indicators`);
        
        // 方案4: 时间序列集合
        console.log('\n=== 方案4: 时间序列集合 ===');
        await optimizer.createTimeSeriesCollection();
        
    } finally {
        await optimizer.disconnect();
    }
}

// 如果直接运行此文件，执行示例
if (require.main === module) {
    main().catch(console.error);
}

module.exports = StockIndicatorOptimizer;
