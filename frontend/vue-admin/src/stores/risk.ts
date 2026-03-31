import { defineStore } from 'pinia'
import { reactive } from 'vue'
import { apiRisk, type RiskReport } from '../services/api_risk'

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

  function clearCurrentReport() {
    state.currentReport = null
  }

  return {
    state,
    fetchReports,
    fetchReport,
    clearCurrentReport,
  }
})
