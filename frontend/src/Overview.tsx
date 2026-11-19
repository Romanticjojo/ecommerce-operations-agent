import { useState } from 'react'
import { ArrowRight, ArrowUpRight } from 'lucide-react'
import type { Overview as OverviewData } from './api'
import { dateOnly, number, percent, sourceName } from './api'
import { BarChart, Empty, ErrorBox, Fold, PageHead, Pending, Table, Trend } from './ui'

export function Overview({ data, error, retry }: { data?: OverviewData; error: string; retry: () => void }) {
  const [metric, setMetric] = useState<'item_revenue' | 'order_count'>('item_revenue')
  const coverage = data && [sourceName(data.source), data.start && data.end
    ? `订单购买日期　${dateOnly(data.start)} — ${dateOnly(data.end)}` : '购买日期未记录'].join('　·　')
  return <div className="overview-report">
    <PageHead title="运营概览" sub={coverage} action={<a className="primary" href="#ask">开始分析<ArrowRight size={16}/></a>}/>
    {error ? <ErrorBox message={error} retry={retry}/> : !data ? <Pending/> :
      !data.order_count && !data.monthly?.length ? <div className="panel"><Empty title="尚无已送达订单" action={<a className="quiet" href="#data">查看数据准备说明<ArrowRight size={15}/></a>}>导入包含有效订单的数据快照后即可查看经营表现。</Empty></div> :
      <>
        <div className="sales-spread">
          <section className="sales-total">
            <h2>商品成交额 <small>BRL</small></h2>
            <strong className="report-amount">{number(data.item_revenue, 2)}</strong>
            <p>按已送达订单汇总商品价格，不含运费。</p>
            <dl className="sales-context">
              <div><dt>已送达订单</dt><dd><strong>{number(data.order_count)}</strong> 单</dd></div>
              <div><dt>平均客单价</dt><dd><strong>{number(data.aov, 2)}</strong> BRL</dd></div>
            </dl>
          </section>
          <section className="sales-trend">
            <div className="panel-head"><h2>月度经营趋势</h2>
              <div className="seg" role="group" aria-label="趋势指标">{(['item_revenue', 'order_count'] as const).map((m, i) =>
                <button key={m} aria-pressed={metric === m} onClick={() => setMetric(m)}>{i ? '订单数' : '成交额'}</button>
              )}</div>
            </div>
            <Trend rows={data.monthly || []} x="month" y={metric} unit={metric === 'item_revenue' ? 'BRL' : '单'}/>
            <Fold title="查看月度数据"><Table rows={data.monthly} caption="月度经营趋势数据"/></Fold>
          </section>
        </div>
        <div className="report-details">
          <section className="category-report">
            <div className="panel-head"><h2>品类成交排行</h2><p>前五名 · BRL</p></div>
            <BarChart rows={(data.categories || []).slice(0, 5)} x="category" y="item_revenue" formatter={v => number(v, 2)}/>
            <Fold title="查看品类数据"><Table rows={data.categories} caption="品类成交额"/></Fold>
          </section>
          <section className="delivery-report">
            <h2>配送与差评</h2>
            <div className="review-metric"><strong>{percent(data.negative_rate)}</strong><span>订单差评率</span></div>
            <p>限已送达、配送时间齐全且有有效评价的订单。每单取一条评价，1–2 分计为差评。</p>
            <a className="report-link" href="#investigation">比较延迟与准时送达订单<ArrowRight size={16}/></a>
          </section>
        </div>
        <footer className="report-footer"><a className="report-link" href="#data">查看数据来源与指标口径<ArrowUpRight size={15}/></a></footer>
      </>}
  </div>
}
