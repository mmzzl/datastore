import { defineStore } from 'pinia'
import { reactive } from 'vue'
import { apiQlib, type Model, type TrainingStatus, type SelectionResult, type Instrument, type Experiment, type ExperimentListResult, type BestModel, type TopStocksDay, type TrainingTask } from '../services/api_qlib'

export const useQlibStore = defineStore('qlib', () => {
  const state = reactive({
    models: [] as Model[],
    currentModel: null as Model | null,
    trainingStatus: null as TrainingStatus | null,
    selectionResults: null as SelectionResult | null,
  csi300Instruments: [] as Instrument[],
  experiments: [] as Experiment[],
  experimentsTotal: 0,
  experimentsPage: 1,
  bestModel: null as BestModel | null,
  topStocks: [] as TopStocksDay[],
  topStocksTotal: 0,
  topStocksPage: 1,
  refreshingTopStocks: false,
  trainingTasks: [] as TrainingTask[],
  trainingTasksTotal: 0,
  loading: false,
    training: false,
    selecting: false,
    error: null as string | null,
  })

  async function fetchModels() {
    state.loading = true
    state.error = null
    try {
      const res = await apiQlib.getModels()
      state.models = res.items || []
    } catch (e: any) {
      state.error = e.response?.data?.detail || '获取模型列表失败'
    } finally {
      state.loading = false
    }
  }

  async function fetchModel(id: string) {
    state.loading = true
    state.error = null
    try {
      state.currentModel = await apiQlib.getModel(id)
    } catch (e: any) {
      state.error = e.response?.data?.detail || '获取模型详情失败'
    } finally {
      state.loading = false
    }
  }

  async function startTraining(request: Parameters<typeof apiQlib.startTraining>[0]) {
    state.training = true
    state.error = null
    try {
      const res = await apiQlib.startTraining(request)
      state.trainingStatus = {
        id: res.id,
        status: 'pending',
        progress: 0
      }
      return res.id
    } catch (e: any) {
      state.error = e.response?.data?.detail || '启动训练失败'
      throw e
    } finally {
      state.training = false
    }
  }

  async function checkTrainingStatus(id: string) {
    try {
      state.trainingStatus = await apiQlib.getTrainingStatus(id)
      return state.trainingStatus
    } catch (e: any) {
      state.error = e.response?.data?.detail || '获取训练状态失败'
      throw e
    }
  }

  async function runSelection(request: Parameters<typeof apiQlib.runSelection>[0]) {
    state.selecting = true
    state.error = null
    try {
      state.selectionResults = await apiQlib.runSelection(request)
      return state.selectionResults
    } catch (e: any) {
      state.error = e.response?.data?.detail || '股票筛选失败'
      throw e
    } finally {
      state.selecting = false
    }
  }

  async function fetchCSI300() {
    state.loading = true
    state.error = null
    try {
      state.csi300Instruments = await apiQlib.getCSI300()
    } catch (e: any) {
      state.error = e.response?.data?.detail || '获取沪深300成分股失败'
    } finally {
      state.loading = false
    }
  }

  function clearSelectionResults() {
    state.selectionResults = null
  }

  function clearTrainingStatus() {
    state.trainingStatus = null
  }

  async function fetchExperiments(page: number = 1, pageSize: number = 20, tag?: string, status?: string) {
    state.loading = true
    state.error = null
    try {
      const res = await apiQlib.getExperiments(page, pageSize, tag, status)
      state.experiments = res.items
      state.experimentsTotal = res.total
      state.experimentsPage = page
    } catch (e: any) {
      state.error = e.response?.data?.detail || '获取实验列表失败'
    } finally {
      state.loading = false
    }
  }

  async function fetchBestModel() {
    state.loading = true
    state.error = null
    try {
      state.bestModel = await apiQlib.getBestModel()
    } catch (e: any) {
      state.error = e.response?.data?.detail || '获取最优模型失败'
    } finally {
      state.loading = false
    }
  }

  async function fetchTopStocks(startDate?: string, endDate?: string, modelId?: string, page: number = 1, pageSize: number = 20) {
    state.loading = true
    state.error = null
    try {
      const res = await apiQlib.getTopStocks(startDate, endDate, modelId, page, pageSize)
      state.topStocks = res.items
      state.topStocksTotal = res.total
      state.topStocksPage = page
    } catch (e: any) {
      state.error = e.response?.data?.detail || '获取Top10推荐失败'
    } finally {
      state.loading = false
    }
  }

  async function refreshTopStocks() {
    state.refreshingTopStocks = true
    state.error = null
    try {
      await apiQlib.refreshTopStocks()
      const today = new Date().toISOString().split('T')[0]
      await fetchTopStocks(today, today, undefined, 1)
    } catch (e: any) {
      state.error = e.response?.data?.detail || '刷新Top10失败'
    } finally {
      state.refreshingTopStocks = false
    }
  }

  async function fetchTrainingTasks(page: number = 1, pageSize: number = 20) {
    state.loading = true
    state.error = null
    try {
      const res = await apiQlib.getTrainingTasks(page, pageSize)
      state.trainingTasks = res.items
      state.trainingTasksTotal = res.total
    } catch (e: any) {
      state.error = e.response?.data?.detail || '获取训练任务列表失败'
    } finally {
      state.loading = false
    }
  }

  async function revokeTask(taskId: string) {
    try {
      await apiQlib.revokeTrainingTask(taskId)
      await fetchTrainingTasks()
    } catch (e: any) {
      state.error = e.response?.data?.detail || '取消任务失败'
    }
  }

  async function rerunTask(taskId: string) {
    try {
      await apiQlib.rerunTrainingTask(taskId)
      await fetchTrainingTasks()
    } catch (e: any) {
      state.error = e.response?.data?.detail || '重跑任务失败'
    }
  }

  return {
    state,
    fetchModels,
    fetchModel,
    startTraining,
    checkTrainingStatus,
    runSelection,
    fetchCSI300,
    clearSelectionResults,
    clearTrainingStatus,
    fetchExperiments,
    fetchBestModel,
    fetchTopStocks,
    refreshTopStocks,
    fetchTrainingTasks,
    revokeTask,
    rerunTask,
  }
})
