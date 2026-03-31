import { defineStore } from 'pinia'
import { reactive } from 'vue'
import { apiBacktest, type BacktestResult, type BacktestTrade } from '../services/api_backtest'
import { createWebSocket, type WebSocketManager } from '../services/websocket'

export const useBacktestStore = defineStore('backtest', () => {
  const state = reactive({
    results: [] as BacktestResult[],
    currentBacktest: null as BacktestResult | null,
    progress: 0,
    status: 'idle' as 'idle' | 'pending' | 'running' | 'completed' | 'failed',
    wsConnected: false,
    loading: false,
    error: null as string | null,
    currentPage: 1,
    pageSize: 10,
    totalPages: 0,
    totalCount: 0,
  })

  let ws: WebSocketManager | null = null

  async function fetchResults(page: number = 1) {
    state.loading = true
    state.error = null
    try {
      const res = await apiBacktest.getResults(page, state.pageSize)
      state.results = res.items || []
      state.currentPage = res.page || 1
      state.totalPages = res.total_pages || 0
      state.totalCount = res.total || 0
    } catch (e: any) {
      state.error = e.response?.data?.detail || '获取回测结果失败'
    } finally {
      state.loading = false
    }
  }

  async function fetchResult(id: string) {
    state.loading = true
    state.error = null
    try {
      state.currentBacktest = await apiBacktest.getResult(id)
    } catch (e: any) {
      state.error = e.response?.data?.detail || '获取回测详情失败'
    } finally {
      state.loading = false
    }
  }

  async function startBacktest(request: Parameters<typeof apiBacktest.startBacktest>[0]) {
    state.error = null
    state.status = 'pending'
    state.progress = 0
    try {
      const res = await apiBacktest.startBacktest(request)
      state.status = 'running'
      return res.id
    } catch (e: any) {
      state.status = 'failed'
      state.error = e.response?.data?.detail || '启动回测失败'
      throw e
    }
  }

  function connectWebSocket(backtestId?: string) {
    if (ws) {
      ws.disconnect()
    }

    ws = createWebSocket({
      url: '/ws/backtest' + (backtestId ? `/${backtestId}` : ''),
      onOpen: () => {
        state.wsConnected = true
      },
      onClose: () => {
        state.wsConnected = false
      },
      onMessage: (data) => {
        if (data.type === 'progress') {
          state.progress = data.progress
          state.status = 'running'
        } else if (data.type === 'completed') {
          state.status = 'completed'
          state.progress = 100
          if (data.result) {
            state.currentBacktest = data.result
          }
          fetchResults(state.currentPage)
        } else if (data.type === 'error') {
          state.status = 'failed'
          state.error = data.message
        }
      },
      onError: (error) => {
        console.error('WebSocket error:', error)
        state.wsConnected = false
      },
    })

    ws.connect()
  }

  function disconnectWebSocket() {
    if (ws) {
      ws.disconnect()
      ws = null
      state.wsConnected = false
    }
  }

  function reset() {
    state.status = 'idle'
    state.progress = 0
    state.currentBacktest = null
    state.error = null
  }

  return {
    state,
    fetchResults,
    fetchResult,
    startBacktest,
    connectWebSocket,
    disconnectWebSocket,
    reset,
  }
})
