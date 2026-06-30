<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import { X } from 'lucide-vue-next'
import { useLedgerStore } from '../stores/ledger'
import type { EntryType, Transaction } from '../types'
import { centsToYuan, yuanToCents } from '../utils/format'

const props = defineProps<{
  open: boolean
  transaction: Transaction | null
}>()

const emit = defineEmits<{
  close: []
  saved: []
}>()

const ledger = useLedgerStore()

const form = reactive({
  id: undefined as number | undefined,
  type: 'expense' as EntryType,
  amount: '',
  categoryId: 1,
  transactionDate: new Date().toISOString().slice(0, 10),
  note: '',
})

const title = computed(() => (form.id ? '编辑账单' : '新增账单'))
const categories = computed(() => ledger.categoriesByType(form.type))
const canSave = computed(() => yuanToCents(form.amount) > 0 && Boolean(form.categoryId) && Boolean(form.transactionDate))

watch(
  () => props.open,
  (open) => {
    if (!open) return
    if (props.transaction) {
      form.id = props.transaction.id
      form.type = props.transaction.type
      form.amount = centsToYuan(props.transaction.amount)
      form.categoryId = props.transaction.categoryId
      form.transactionDate = props.transaction.transactionDate
      form.note = props.transaction.note
      return
    }
    form.id = undefined
    form.type = 'expense'
    form.amount = ''
    form.categoryId = ledger.expenseCategories[0]?.id || 1
    form.transactionDate = `${ledger.currentMonth}-${String(new Date().getDate()).padStart(2, '0')}`
    form.note = ''
  },
)

watch(
  () => form.type,
  (type) => {
    const available = ledger.categoriesByType(type)
    if (!available.some((category) => category.id === form.categoryId)) {
      form.categoryId = available[0]?.id || form.categoryId
    }
  },
)

const save = () => {
  if (!canSave.value) return
  ledger.saveTransaction({
    id: form.id,
    type: form.type,
    amount: yuanToCents(form.amount),
    categoryId: form.categoryId,
    transactionDate: form.transactionDate,
    note: form.note.trim(),
  })
  emit('saved')
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="modal-backdrop" @click.self="emit('close')">
      <section class="sheet" aria-modal="true" role="dialog">
        <header class="sheet-header">
          <button class="icon-button ghost" type="button" aria-label="关闭" @click="emit('close')">
            <X :size="20" />
          </button>
          <h2>{{ title }}</h2>
          <button class="text-button" type="button" :disabled="!canSave" @click="save">保存</button>
        </header>

        <div class="field-group">
          <label>类型</label>
          <div class="segmented">
            <button type="button" :class="{ active: form.type === 'expense' }" @click="form.type = 'expense'">支出</button>
            <button type="button" :class="{ active: form.type === 'income' }" @click="form.type = 'income'">收入</button>
          </div>
        </div>

        <label class="field">
          <span>金额</span>
          <input v-model="form.amount" inputmode="decimal" placeholder="0.00" />
        </label>

        <div class="field-group">
          <label>分类</label>
          <div class="chip-grid">
            <button
              v-for="category in categories"
              :key="category.id"
              type="button"
              class="chip"
              :class="{ active: category.id === form.categoryId }"
              @click="form.categoryId = category.id"
            >
              {{ category.name }}
            </button>
          </div>
        </div>

        <label class="field">
          <span>日期</span>
          <input v-model="form.transactionDate" type="date" />
        </label>

        <label class="field">
          <span>备注</span>
          <input v-model="form.note" maxlength="40" placeholder="选填，例如：午餐" />
        </label>
      </section>
    </div>
  </Teleport>
</template>
