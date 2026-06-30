<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { PieChart } from 'echarts/charts'
import { LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { ECharts } from 'echarts/core'
import { formatMoney } from '../utils/format'

echarts.use([PieChart, TooltipComponent, LegendComponent, CanvasRenderer])

const props = defineProps<{
  data: Array<{ name: string; amount: number; ratio: number }>
}>()

const chartEl = ref<HTMLDivElement | null>(null)
let chart: ECharts | null = null

const hasData = computed(() => props.data.length > 0)

const render = () => {
  if (!chartEl.value || !hasData.value) return
  chart ||= echarts.init(chartEl.value)
  chart.setOption({
    color: ['#ef7d42', '#3f8cff', '#20a06b', '#f2b84b', '#8a6de9', '#d95c82'],
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => `${params.name}<br/>${formatMoney(params.value)} (${params.percent}%)`,
    },
    legend: {
      bottom: 0,
      itemWidth: 8,
      itemHeight: 8,
      textStyle: { color: '#6b7280', fontSize: 12 },
    },
    series: [
      {
        name: '分类支出',
        type: 'pie',
        radius: ['46%', '68%'],
        center: ['50%', '42%'],
        avoidLabelOverlap: true,
        label: {
          formatter: '{b}\n{d}%',
          color: '#28313f',
          fontSize: 12,
        },
        labelLine: { length: 8, length2: 6 },
        data: props.data.map((item) => ({ name: item.name, value: item.amount })),
      },
    ],
  })
}

watch(() => props.data, render, { deep: true })

onMounted(() => {
  render()
  window.addEventListener('resize', render)
})

onUnmounted(() => {
  window.removeEventListener('resize', render)
  chart?.dispose()
})
</script>

<template>
  <div class="chart-shell">
    <div v-if="hasData" ref="chartEl" class="chart"></div>
    <div v-else class="empty-chart">
      <span>暂无支出</span>
      <strong>本月还没有消费记录</strong>
    </div>
  </div>
</template>
