<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Plus, Trash2 } from 'lucide-vue-next'
import { useLedgerStore } from '../stores/ledger'
import type { Category, EntryType } from '../types'

const router = useRouter()
const ledger = useLedgerStore()

const name = ref('')
const type = ref<EntryType>('expense')
const editingId = ref<number | null>(null)

const defaultCategories = computed(() => ledger.categories.filter((category) => category.is_default))
const customCategories = computed(() => ledger.categories.filter((category) => !category.is_default))

const resetForm = () => {
  name.value = ''
  type.value = 'expense'
  editingId.value = null
}

const editCategory = (category: Category) => {
  if (category.is_default) return
  editingId.value = category.id
  name.value = category.name
  type.value = category.type
}

const saveCategory = async () => {
  if (!name.value.trim()) return
  if (editingId.value) {
    await ledger.updateCategory(editingId.value, name.value, type.value)
  } else {
    await ledger.createCategory(name.value, type.value)
  }
  resetForm()
}

const deactivate = async (category: Category) => {
  if (window.confirm(`停用分类 ${category.name}？`)) {
    await ledger.deactivateCategory(category.id)
  }
}

onMounted(() => {
  ledger.loadCategories(true)
})
</script>

<template>
  <main class="app-shell">
    <section class="phone-frame">
      <header class="topbar compact">
        <button class="icon-button" type="button" aria-label="返回首页" @click="router.push({ name: 'home' })">
          <ArrowLeft :size="20" />
        </button>
        <h1>分类管理</h1>
        <span class="topbar-spacer"></span>
      </header>

      <section class="panel">
        <div class="section-title">
          <h2>默认分类</h2>
          <span>开箱即用</span>
        </div>
        <div class="category-list">
          <span v-for="category in defaultCategories" :key="category.id" class="category-pill" :class="category.type">
            {{ category.name }}
          </span>
        </div>
      </section>

      <section class="panel">
        <div class="section-title">
          <h2>自定义分类</h2>
          <span>{{ customCategories.length }} 个</span>
        </div>
        <div v-if="customCategories.length" class="category-stack">
          <div v-for="category in customCategories" :key="category.id" class="category-admin-row" :class="{ inactive: !category.is_active }">
            <button type="button" class="category-pill" :class="category.type" @click="editCategory(category)">
              {{ category.name }}{{ category.is_active ? '' : '（已停用）' }}
            </button>
            <button
              v-if="category.is_active"
              class="icon-button danger"
              type="button"
              aria-label="停用分类"
              @click="deactivate(category)"
            >
              <Trash2 :size="17" />
            </button>
          </div>
        </div>
        <div v-else class="empty-state slim">
          <strong>暂无自定义分类</strong>
        </div>
      </section>

      <section class="panel">
        <div class="section-title">
          <h2>{{ editingId ? '编辑分类' : '添加分类' }}</h2>
          <button v-if="editingId" class="text-button" type="button" @click="resetForm">取消</button>
        </div>
        <div class="segmented wide">
          <button type="button" :class="{ active: type === 'expense' }" @click="type = 'expense'">支出</button>
          <button type="button" :class="{ active: type === 'income' }" @click="type = 'income'">收入</button>
        </div>
        <label class="field">
          <span>分类名称</span>
          <input v-model="name" maxlength="12" placeholder="例如：设计设备" @keyup.enter="saveCategory" />
        </label>
        <button class="primary-button" type="button" :disabled="!name.trim()" @click="saveCategory">
          <Plus :size="18" />
          {{ editingId ? '保存分类' : '添加分类' }}
        </button>
      </section>
    </section>
  </main>
</template>
