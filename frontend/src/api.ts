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
    const hint = typeof detail === 'string' ? detail : 'Check the local service and data snapshot, then retry.'
    throw new Error('Request failed (' + res.status + '). ' + hint)
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

export const errorText = (err: unknown) => err instanceof Error ? err.message : 'Connection failed. Check the local service and retry.'
export const number = (n: unknown, digits = 0) => typeof n === 'number' && Number.isFinite(n)
  ? n.toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits }) : '—'
export const percent = (n: unknown) => typeof n === 'number' ? number(n * 100, 1) + '%' : '—'
export const dateOnly = (value?: string | null) => value ? value.slice(0, 10) : '—'
export function display(value: unknown): string {
  if (value == null || value === '') return '—'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (typeof value === 'object') return JSON.stringify(value, null, 2)
  return String(value)
}
export function sourceName(value?: string) {
  if (!value) return 'Dataset'
  if (/synth|fixture|demo/i.test(value)) return 'Synthetic sample'
  return value.toLowerCase() === 'olist' ? 'Olist Brazilian E-Commerce' : value
}
export function modeName(value?: string) {
  if (!value) return 'Checking mode…'
  if (/offline|demo|deterministic/i.test(value)) return 'Offline demo'
  if (value === 'full') return 'Full workflow'
  if (/model|online|live/i.test(value)) return 'Live model'
  if (value === 'statistics') return 'Statistical investigation'
  if (value === 'reference') return 'Reference SQL'
  if (value === 'baseline' || value === 'direct') return 'Baseline model'
  return value
}
const names: Record<string, string> = {
  month: 'Month', category: 'Product category', item_revenue: 'Item revenue (BRL)', order_count: 'Orders',
  aov: 'Average order value (BRL)', negative_rate: 'Negative review rate', risk_difference: 'Difference in negative review rates',
  filters: 'Filters', metric: 'Metric', metrics: 'Metrics', metric_id: 'Metric ID', metric_ids: 'Metric IDs',
  definitions: 'Definitions', metric_definitions: 'Metric definitions', snapshot: 'Snapshot ID', source: 'Data source', grain: 'Grain',
  row_count: 'Rows returned', truncated: 'Result truncated', warnings: 'Warnings', language: 'Answer language',
  timing_ms: 'Elapsed time (ms)', stages: 'Execution stages', mode: 'Mode', model: 'Model', start: 'Start date',
  end: 'End date (exclusive)', answer: 'Answer', status: 'Status', label: 'Label', question: 'Question',
  request_id: 'Request ID', created_at: 'Created at', method: 'Method', accuracy: 'Accuracy',
  imported_at: 'Imported at', name: 'Name', count: 'Count', group: 'Group', n: 'Orders', negative: 'Orders with negative reviews',
  passed: 'Passed', expected: 'Expected', actual: 'Actual', test: 'Statistical test', results: 'Results by question',
  included_orders: 'Included orders', total_orders: 'Orders in scope', not_delivered: 'Undelivered orders', missing_delivery_time: 'Missing delivery timestamps',
  no_valid_review: 'No valid review', missing_values: 'Missing values by field', orphan_foreign_keys: 'Unmatched foreign keys',
  invalid_review_scores: 'Invalid review scores', repeated_review_ids: 'Repeated review IDs', review_ids_on_multiple_orders: 'Review IDs shared by multiple orders',
  orders_with_multiple_eligible_reviews: 'Orders with multiple eligible reviews', delivered_orders_without_items: 'Delivered orders without items',
  type: 'Type', description: 'Description', variant: 'Workflow', total: 'Questions', correct: 'Correct', execution_accuracy: 'Accuracy on answerable questions',
  sql_success_rate: 'SQL success rate', median_ms: 'Median time (ms)', errors: 'Errors by type', reference_sql_count: 'Reference SQL queries',
  human_review: 'Human review', expected_status: 'Expected status', reference_ran: 'Reference SQL executed', expected_rows: 'Expected rows',
  sql_success: 'SQL succeeded', generated_sql: 'SQL generated', error_type: 'Error type', latency_ms: 'Latency (ms)',
  usage: 'Model usage', estimated_cost_usd: 'Estimated cost (USD)', prompt_version: 'Prompt version', rate: 'Negative review rate',
  statistics: 'Statistics', payment_total: 'Payment total (BRL)', freight_value: 'Freight (BRL)', currency: 'Currency', plan: 'Query plan',
  requires_purchase_time: 'Requires purchase timestamp', intent: 'Intent', dimension: 'Grouping', sort: 'Sort order', limit: 'Row limit',
  year: 'Year', state: 'Customer state', delivery_group: 'Delivery group', error_code: 'Error code', repairs: 'Repair attempts',
  model_ms: 'Model time (ms)', sql_ms: 'SQL time (ms)', statistics_ms: 'Statistical analysis time (ms)',
  id: 'ID', ci95: '95% confidence interval', p_value: 'p-value', reviewed_order_count: 'Orders with reviews', negative_count: 'Negative reviews',
}
export const label = (key: string) => names[key] ?? key
export function stateName(state: string) {
  return ({ success: 'Success', ok: 'Success', completed: 'Completed', not_run: 'Not run',
    insufficient_data: 'Insufficient data', no_data: 'No data', clarification_required: 'Clarification needed',
    needs_clarification: 'Clarification needed', refused: 'Declined', rejected: 'Declined', error: 'Execution failed',
    refusal: 'Declined', unsafe_request: 'Declined', reference_only: 'Reference only', model_error: 'Model error',
    failed: 'Failed', running: 'Running', unsupported: 'Unsupported', empty: 'No data',
  } as Record<string, string>)[state] ?? state
}

export function exportJson(value: unknown, name: string) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], { type: 'application/json' }))
  const a = document.createElement('a')
  a.href = url; a.download = 'commerce-lens-' + name.replace(/[^a-z0-9_-]/gi, '-') + '.json'
  a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000)
}
