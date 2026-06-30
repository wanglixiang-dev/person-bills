<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Plus } from 'lucide-vue-next'
import { useLedgerStore } from '../stores/ledger'
import type { EntryType } from '../types'

const router = useRouter()
const ledger = useLedgerStore()

const name = ref('')
const type = ref<EntryType>('expense')

const defaultCategories = computed(() => ledger.categories.filter((category) => category.isDefault))
const customCategories = computed(() => ledger.categories.filter((category) => !category.isDefault))

const addCategory = () => {
  ledger.createCategory(name.value, type.value)
  name.value = ''
}
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
        <div v-if="customCategories.length" class="category-list">
          <span v-for="category in customCategories" :key="category.id" class="category-pill" :class="category.type">
            {{ category.name }}
          </span>
        </div>
        <div v-else class="empty-state slim">
          <strong>暂无自定义分类</strong>
        </div>
      </section>

      <section class="panel">
        <div class="section-title">
          <h2>添加分类</h2>
        </div>
        <div class="segmented wide">
          <button type="button" :class="{ active: type === 'expense' }" @click="type = 'expense'">支出</button>
          <button type="button" :class="{ active: type === 'income' }" @click="type = 'income'">收入</button>
        </div>
        <label class="field">
          <span>分类名称</span>
          <input v-model="name" maxlength="12" placeholder="例如：设计设备" @keyup.enter="addCategory" />
        </label>
        <button class="primary-button" type="button" :disabled="!name.trim()" @click="addCategory">
          <Plus :size="18" />
          添加分类
        </button>
      </section>
    </section>
  </main>
</template>
