import { defineStore } from 'pinia'
import { reactive } from 'vue'
import { apiRisk, type RiskReport, type RiskTrend } from '../services/api_risk'

export const useRiskStore = defineStore('risk', () => {
  const state = reactive({
    reports: [] as RiskReport[],
    currentReport: null as RiskReport | null,
    loading: false,
    error: null as string | null,
    currentPage: 1,
    pageSize: 10,
    totalPages: 0,
    totalCount: 0,
    trendData: null as RiskTrend | null,
  })

  async function fetchReports(page: number = 1, type?: string) {
    state.loading = true
    state.error = null
    try {
      const res = await apiRisk.getReports(page, state.pageSize, type)
      state.reports = res.items || []
      state.currentPage = res.page || 1
      state.totalPages = res.total_pages || 0
      state.totalCount = res.total || 0
    } catch (e: any) {
      state.error = e.response?.data?.detail || '获取风险报告失败'
    } finally {
      state.loading = false
    }
  }

  async function fetchReport(id: string) {
    state.loading = true
    state.error = null
    try {
      state.currentReport = await apiRisk.getReport(id)
    } catch (e: any) {
      state.error = e.response?.data?.detail || '获取报告详情失败'
    } finally {
      state.loading = false
    }
  }

  async function fetchTrend(userId: string, days: number = 30) {
    try {
      state.trendData = await apiRisk.getTrend(userId, days)
    } catch (e: any) {
      console.error('Failed to fetch trend data:', e)
    }
  }

  function clearCurrentReport() {
    state.currentReport = null
  }

  return {
    state,
    fetchReports,
    fetchReport,
    fetchTrend,
    clearCurrentReport,
  }
})
