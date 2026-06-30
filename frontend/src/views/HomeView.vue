<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { LogOut, Plus, Settings2, Trash2 } from 'lucide-vue-next'
import CategoryPieChart from '../components/CategoryPieChart.vue'
import TransactionEditor from '../components/TransactionEditor.vue'
import { useAuthStore } from '../stores/auth'
import { useLedgerStore } from '../stores/ledger'
import type { EntryType, Transaction } from '../types'
import { formatDateLabel, formatMoney, formatMonth } from '../utils/format'

const router = useRouter()
const auth = useAuthStore()
const ledger = useLedgerStore()

const editorOpen = ref(false)
const editingTransaction = ref<Transaction | null>(null)

const summaryCards = computed(() => [
  { label: '收入', value: formatMoney(ledger.summary.income_total), tone: 'income' },
  { label: '支出', value: formatMoney(ledger.summary.expense_total), tone: 'expense' },
  { label: '结余', value: formatMoney(ledger.summary.balance), tone: 'balance' },
])

const chartData = computed(() =>
  ledger.categoryRatios.map((item) => ({ name: item.category_name, amount: item.amount, ratio: item.ratio })),
)

const openCreate = () => {
  editingTransaction.value = null
  editorOpen.value = true
}

const openEdit = (transaction: Transaction) => {
  editingTransaction.value = transaction
  editorOpen.value = true
}

const remove = async (transaction: Transaction) => {
  if (window.confirm(`删除 ${transaction.category_name} ${formatMoney(transaction.amount)}？`)) {
    await ledger.deleteTransaction(transaction.id)
  }
}

const closeEditor = () => {
  editorOpen.value = false
  editingTransaction.value = null
}

const logout = async () => {
  await auth.logout()
  await router.push({ name: 'login' })
}

const applyFilter = async () => {
  await ledger.loadHomeData()
}

const setTypeFilter = async (type: EntryType | '') => {
  ledger.filters.type = type
  await applyFilter()
}

onMounted(() => {
  ledger.loadHomeData()
})
</script>

<template>
  <main class="app-shell">
    <section class="phone-frame">
      <header class="topbar">
        <div>
          <span class="eyebrow">{{ auth.user?.email }}</span>
          <h1>个人记账本</h1>
        </div>
        <div class="topbar-actions">
          <button class="icon-button" type="button" aria-label="分类管理" @click="router.push({ name: 'categories' })">
            <Settings2 :size="19" />
          </button>
          <button class="icon-button" type="button" aria-label="退出登录" @click="logout">
            <LogOut :size="19" />
          </button>
        </div>
      </header>

      <section class="month-strip">
        <button type="button" @click="ledger.shiftMonth(-1)">上一月</button>
        <strong>{{ formatMonth(ledger.currentMonth) }}</strong>
        <button type="button" @click="ledger.shiftMonth(1)">下一月</button>
      </section>

      <section class="summary-grid">
        <article v-for="card in summaryCards" :key="card.label" class="summary-card" :class="card.tone">
          <span>{{ card.label }}</span>
          <strong>{{ card.value }}</strong>
        </article>
      </section>

      <section class="panel">
        <div class="section-title">
          <h2>分类支出占比</h2>
          <span v-if="ledger.categoryRatios.length">{{ ledger.categoryRatios.length }} 类支出</span>
        </div>
        <CategoryPieChart :data="chartData" />
        <div v-if="ledger.categoryRanking.length" class="ranking-list">
          <div v-for="item in ledger.categoryRanking" :key="item.category_id" class="ranking-row">
            <span>{{ item.rank }}. {{ item.category_name }}</span>
            <strong>{{ formatMoney(item.amount) }} · {{ item.ratio }}%</strong>
          </div>
        </div>
      </section>

      <section class="panel">
        <div class="section-title">
          <h2>近6个月趋势</h2>
        </div>
        <div class="trend-list">
          <div v-for="item in ledger.sixMonthTrend" :key="item.month" class="trend-row">
            <span>{{ item.month }}</span>
            <strong>收 {{ formatMoney(item.income_total) }}</strong>
            <strong>支 {{ formatMoney(item.expense_total) }}</strong>
          </div>
        </div>
      </section>

      <section class="panel list-panel">
        <div class="section-title">
          <h2>账单列表</h2>
          <span>{{ ledger.monthTransactions.length }} 笔</span>
        </div>

        <div class="filters">
          <div class="segmented">
            <button type="button" :class="{ active: ledger.filters.type === '' }" @click="setTypeFilter('')">全部</button>
            <button type="button" :class="{ active: ledger.filters.type === 'expense' }" @click="setTypeFilter('expense')">支出</button>
            <button type="button" :class="{ active: ledger.filters.type === 'income' }" @click="setTypeFilter('income')">收入</button>
          </div>
          <select v-model.number="ledger.filters.category_id" @change="applyFilter">
            <option :value="null">全部分类</option>
            <option v-for="category in ledger.categories" :key="category.id" :value="category.id">{{ category.name }}</option>
          </select>
        </div>

        <div v-if="ledger.monthTransactions.length" class="transaction-list">
          <article
            v-for="transaction in ledger.monthTransactions"
            :key="transaction.id"
            class="transaction-row"
            @click="openEdit(transaction)"
          >
            <div class="transaction-main">
              <div class="category-dot" :class="transaction.type"></div>
              <div>
                <strong>{{ transaction.category_name }}</strong>
                <span>{{ transaction.note || '无备注' }} · {{ formatDateLabel(transaction.transaction_date) }}</span>
              </div>
            </div>
            <div class="transaction-side">
              <strong :class="transaction.type">
                {{ transaction.type === 'income' ? '+' : '-' }}{{ formatMoney(transaction.amount) }}
              </strong>
              <button class="icon-button danger" type="button" aria-label="删除账单" @click.stop="remove(transaction)">
                <Trash2 :size="17" />
              </button>
            </div>
          </article>
        </div>

        <div v-else class="empty-state">
          <strong>这个月份还没有账单</strong>
          <span>点击右下角按钮记录第一笔收支</span>
        </div>
      </section>

      <button class="fab" type="button" aria-label="新增账单" :disabled="ledger.loading || !ledger.categories.length" @click="openCreate">
        <Plus :size="28" />
      </button>
    </section>

    <TransactionEditor
      :open="editorOpen"
      :transaction="editingTransaction"
      @close="closeEditor"
      @saved="closeEditor"
    />
  </main>
</template>
