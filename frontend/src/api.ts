import { useCallback, useEffect, useState } from 'react'

export type Row = Record<string, unknown>
export interface Overview {
  source: string; snapshot: string; order_count: number; item_revenue: number | null; aov: number | null
  negative_rate: number | null; start: string | null; end: string | null
  monthly: { month: string; order_count: number; item_revenue: number; aov: number | null }[]
  categories: { category: string; item_revenue: number }[]
}
export interface Config { configured: boolean; model: string | null; mode: string }
export interface Catalog {
  source: string; snapshot: string; tables: { name: string; rows: number; grain: string; columns: unknown[] }[]
  metrics: { id: string; label: string; definition: string }[]; quality: Row; imported_at?: string; audit?: { imported_at?: string }
}
export interface Answer {
  request_id: string; question: string; status: string; answer: string; table: Row[]
  chart?: { type: string; x: string; y: string } | null; evidence: Row; mode: string; timing_ms: number
}
export interface Investigation {
  status: string; groups: { group: string; n: number; negative: number; rate: number | null }[]
  risk_difference: number | null; ci95: [number, number] | null; p_value: number | null
  test: string | null; exclusions: unknown; limitations: unknown; sql: string; request_id: string
  grain?: string; snapshot_id?: string; filters?: Row; review_records?: { n: number; negative: number; rate: number | null }; review_records_sql?: string; exclusions_sql?: string
}
export interface Evaluation { status: string; summary: Row[]; results: Row[]; [key: string]: unknown }
export interface Run { request_id: string; question: string; status: string; mode: string; created_at: string }

export async function api<T>(path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  const res = await fetch('/api/' + path, {
    method: body === undefined ? 'GET' : 'POST', signal,
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!res.ok) {
    let detail
    try { detail = (await res.json()).detail } catch { /* Non-JSON upstream response. */ }
    const hint = typeof detail === 'string' ? detail : '请检查本地服务和数据快照，然后重试。'
    throw new Error('请求未完成（' + res.status + '）。' + hint)
  }
  return res.json()
}

export function useResource<T>(path: string) {
  const [data, setData] = useState<T>()
  const [error, setError] = useState('')
  const [version, setVersion] = useState(0)
  const retry = useCallback(() => setVersion(n => n + 1), [])
  useEffect(() => {
    const ctrl = new AbortController()
    setData(undefined); setError('')
    api<T>(path, undefined, ctrl.signal)
      .then(value => { if (!ctrl.signal.aborted) setData(value) })
      .catch(err => { if (!ctrl.signal.aborted) setError(errorText(err)) })
    return () => ctrl.abort()
  }, [path, version])
  return { data, error, retry }
}

export const errorText = (err: unknown) => err instanceof Error ? err.message : '服务连接失败，请检查本地服务并重试。'
export const number = (n: unknown, digits = 0) => typeof n === 'number' && Number.isFinite(n)
  ? n.toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits }) : '—'
export const percent = (n: unknown) => typeof n === 'number' ? number(n * 100, 1) + '%' : '—'
export const dateOnly = (value?: string | null) => value ? value.slice(0, 10).replaceAll('-', '.') : '—'
export function display(value: unknown): string {
  if (value == null || value === '') return '—'
  if (typeof value === 'boolean') return value ? '是' : '否'
  if (typeof value === 'object') return JSON.stringify(value, null, 2)
  return String(value)
}
export function sourceName(value?: string) {
  if (!value) return '数据集'
  if (/synth|fixture|demo|示例|合成/i.test(value)) return '合成示例数据'
  return value.toLowerCase() === 'olist' ? 'Olist 数据集' : value
}
export function modeName(value?: string) {
  if (!value) return '模式待确认'
  if (/offline|demo|deterministic/i.test(value)) return '离线演示'
  if (/full|model|online|live/i.test(value)) return '模型分析'
  if (value === 'statistics') return '统计调查'
  if (value === 'reference') return '参考 SQL'
  if (value === 'baseline' || value === 'direct') return '基线模型'
  return value
}
const names: Record<string, string> = {
  month: '月份', category: '商品品类', item_revenue: '商品成交额（BRL）', order_count: '订单数',
  aov: '客单价（BRL）', negative_rate: '差评率', risk_difference: '差评率差值', filters: '筛选条件',
  metric: '指标', metrics: '指标', metric_id: '指标 ID', metric_ids: '指标 ID', definitions: '指标定义',
  metric_definitions: '指标定义', snapshot: '数据快照', source: '数据来源', grain: '数据粒度',
  row_count: '返回行数', truncated: '结果已截断', warnings: '提示', language: '回答语言',
  timing_ms: '耗时（ms）', stages: '执行阶段', mode: '运行模式', model: '模型', start: '开始日期',
  end: '结束日期（不含）', answer: '回答', status: '状态', label: '名称', question: '问题',
  request_id: '请求 ID', created_at: '创建时间', method: '方法', accuracy: '准确率',
  imported_at: '导入时间', name: '名称', count: '数量', group: '分组', n: '订单数', negative: '差评订单数',
  passed: '通过', expected: '预期', actual: '实际', test: '检验方法', results: '逐题记录',
  included_orders: '纳入订单', total_orders: '范围内订单', not_delivered: '未送达订单', missing_delivery_time: '缺少配送时间',
  no_valid_review: '无有效评价', missing_values: '缺失字段计数', orphan_foreign_keys: '缺少对应主表记录',
  invalid_review_scores: '无效评分记录', repeated_review_ids: '重复评价编号', review_ids_on_multiple_orders: '跨订单评价编号',
  orders_with_multiple_eligible_reviews: '有多条有效评价的订单', delivered_orders_without_items: '无商品明细的已送达订单',
  type: '类型', description: '字段说明', variant: '评估方法', total: '题数', correct: '正确', execution_accuracy: '可回答题准确率',
  sql_success_rate: 'SQL 成功率', median_ms: '耗时中位数（ms）', errors: '错误分类', reference_sql_count: '参考 SQL 数',
  human_review: '人工审核', expected_status: '预期状态', reference_ran: '参考 SQL 已执行', expected_rows: '预期行数',
  sql_success: 'SQL 成功', generated_sql: '已生成 SQL', error_type: '错误类型', latency_ms: '耗时（ms）',
  usage: '模型用量', estimated_cost_usd: '估算费用（USD）', prompt_version: '提示词版本', rate: '差评率', statistics: '统计结果',
  payment_total: '支付金额（BRL）', freight_value: '运费（BRL）',
}
export const label = (key: string) => names[key] ?? key
export function stateName(state: string) {
  return ({ success: '成功', ok: '成功', completed: '已完成', not_run: '尚未运行',
    insufficient_data: '样本不足', no_data: '无数据', clarification_required: '需要澄清',
    needs_clarification: '需要澄清', refused: '已拒绝', rejected: '已拒绝', error: '执行失败',
    refusal: '已拒绝', unsafe_request: '已拒绝', reference_only: '参考查询', model_error: '模型服务异常', failed: '失败', running: '运行中', unsupported: '暂不支持', empty: '无数据',
  } as Record<string, string>)[state] ?? state
}

export function exportJson(value: unknown, name: string) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], { type: 'application/json' }))
  const a = document.createElement('a')
  a.href = url; a.download = 'commerce-lens-' + name.replace(/[^a-z0-9_-]/gi, '-') + '.json'
  a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000)
}
