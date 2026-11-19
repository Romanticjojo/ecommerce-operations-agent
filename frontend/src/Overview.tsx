import { useState } from 'react'
import { ArrowRight, ArrowUpRight, CalendarDays, ChartColumnIncreasing, CircleDollarSign, Database, Layers3, MessageSquareWarning, PackageCheck, ReceiptText, ScanSearch, Sparkles } from 'lucide-react'
import type { Overview as OverviewData } from './api'
import { dateOnly, number, percent, sourceName } from './api'
import { BarChart, Empty, ErrorBox, Fold, PageHead, Pending, Table, Trend } from './ui'

export function Overview({ data, error, retry }: { data?: OverviewData; error: string; retry: () => void }) {
  const [metric, setMetric] = useState<'item_revenue' | 'order_count'>('item_revenue')
  const cards = data && [
    { name: '商品成交额', value: number(data.item_revenue, 2), unit: 'BRL', foot: '已送达订单 · 不含运费', icon: CircleDollarSign, color: 'blue' },
    { name: '已送达订单', value: number(data.order_count), unit: '单', foot: '按订单编号去重', icon: PackageCheck, color: 'teal' },
    { name: '平均客单价', value: number(data.aov, 2), unit: 'BRL', foot: '商品成交额 ÷ 订单数', icon: ReceiptText, color: 'purple' },
    { name: '差评率', value: percent(data.negative_rate), unit: '', foot: '每单一评 · 1–2 分占比', icon: MessageSquareWarning, color: 'orange' },
  ]
  return <>
    <PageHead title="运营概览" sub="欢迎回来，查看当前数据快照的经营表现。" action={<a className="primary" href="#ask"><Sparkles size={17}/>开始分析<ArrowRight size={16}/></a>}/>
    {error ? <ErrorBox message={error} retry={retry}/> : !data ? <Pending/> : <>
      <div className="dateline"><span><Database size={15}/>{sourceName(data.source)}</span><i/><span><CalendarDays size={15}/>{dateOnly(data.start)} — {dateOnly(data.end)}</span></div>
      {!data.order_count && !data.monthly?.length ? <div className="panel"><Empty title="尚无已送达订单" action={<a className="quiet" href="#data">查看数据准备说明<ArrowRight size={15}/></a>}>导入包含有效订单的数据快照后即可查看经营表现。</Empty></div> : <>
        <div className="metrics">{cards?.map(c => <article className="metric-card" key={c.name}><div className="metric-heading"><span className={'icon-tile ' + c.color}><c.icon size={19}/></span><h2>{c.name}</h2><span className="metric-unit">{c.unit}</span></div><div className={'metric-value' + (c.value.length > 9 ? ' long-value' : '')}>{c.value}</div><div className="metric-foot">{c.foot}</div></article>)}</div>
        <div className="chart-row">
          <section className="panel chart-panel"><div className="panel-head"><div><h2>月度经营趋势</h2><p>按订单购买月份汇总</p></div><div className="seg" aria-label="趋势指标">{(['item_revenue', 'order_count'] as const).map((m,i) => <button key={m} aria-pressed={metric === m} onClick={() => setMetric(m)}>{i ? '订单数' : '成交额'}</button>)}</div></div>
            <Trend rows={data.monthly || []} x="month" y={metric} unit={metric === 'item_revenue' ? 'BRL' : '单'}/>
            <Fold title="查看月度数据"><Table rows={data.monthly} caption="月度经营趋势数据"/></Fold>
          </section>
          <section className="panel chart-panel"><div className="panel-head"><div><h2>品类成交排行</h2><p>前五名 · 商品成交额（BRL）</p></div><span className="quiet-icon"><ChartColumnIncreasing size={19}/></span></div><BarChart rows={(data.categories || []).slice(0, 5)} x="category" y="item_revenue" formatter={v => number(v, 2)}/><Fold title="查看品类数据"><Table rows={data.categories} caption="品类成交额"/></Fold></section>
        </div>
      </>}
      <section className="quick-section"><h2>深入探索</h2><div className="quick-grid">
        <a className="quick-link" href="#investigation"><span className="quick-icon teal"><ScanSearch size={22}/></span><span><strong>配送与差评调查</strong><small>比较延迟与准时送达订单的差评率</small></span><ArrowUpRight size={17}/></a>
        <a className="quick-link" href="#data"><span className="quick-icon blue"><Layers3 size={22}/></span><span><strong>数据与指标</strong><small>检查源表、数据质量与指标口径</small></span><ArrowUpRight size={17}/></a>
      </div></section>
    </>}
  </>
}
