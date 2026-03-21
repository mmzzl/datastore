package piepeline

type Pipeline struct {
	Stages []Stage
	sink Sink 
 }

type Stage interface {
	Process(ctx context.Context, data interface{}) (interface{}, error)
}


// 内置Stage 
type ClearStage struct{} // 数据清洗，（去空格，转编码）
type TransformStage struct{} // 数据转换，（JSON 转结构体）
type ValidateStage struct{} // 数据验证，（检查字段是否存在）
type EnrichStage struct{} // 数据丰富，（添加额外字段）