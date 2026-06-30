<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { KeyRound, Mail, ShieldCheck } from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const pageMode = ref<'register' | 'login'>('register')
const loginMode = ref<'code' | 'password'>('code')
const email = ref(`demo-${Date.now()}@example.com`)
const code = ref('')
const password = ref('Password123')
const notice = ref('开发环境验证码固定为 246810')
const loading = ref(false)

const canSubmit = computed(() => {
  if (!email.value.includes('@')) return false
  if (pageMode.value === 'register') return code.value.length === 6 && (!password.value || password.value.length >= 8)
  return loginMode.value === 'code' ? code.value.length === 6 : password.value.length >= 8
})

const sendCode = async () => {
  loading.value = true
  try {
    const sent = await auth.sendCode(email.value, pageMode.value === 'register' ? 'register' : 'login')
    code.value = sent || ''
    notice.value = sent ? `验证码已填入：${sent}` : '验证码已发送'
  } catch (err: any) {
    notice.value = err.message || '验证码发送失败'
  } finally {
    loading.value = false
  }
}

const submit = async () => {
  if (!canSubmit.value) return
  loading.value = true
  try {
    if (pageMode.value === 'register') {
      await auth.register(email.value, code.value, password.value)
    } else if (loginMode.value === 'code') {
      await auth.loginByCode(email.value, code.value)
    } else {
      await auth.loginByPassword(email.value, password.value)
    }
    await router.push({ name: 'home' })
  } catch (err: any) {
    notice.value = err.message || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="auth-page">
    <section class="phone-frame auth-panel">
      <div class="brand-lockup">
        <div class="brand-icon"><ShieldCheck :size="26" /></div>
        <div>
          <h1>个人记账本</h1>
          <p>快速记录日常收支，查看本月消费结构</p>
        </div>
      </div>

      <div class="login-card">
        <div class="segmented wide">
          <button type="button" :class="{ active: pageMode === 'register' }" @click="pageMode = 'register'">注册</button>
          <button type="button" :class="{ active: pageMode === 'login' }" @click="pageMode = 'login'">登录</button>
        </div>

        <div v-if="pageMode === 'login'" class="segmented wide">
          <button type="button" :class="{ active: loginMode === 'code' }" @click="loginMode = 'code'">
            <Mail :size="16" />
            验证码
          </button>
          <button type="button" :class="{ active: loginMode === 'password' }" @click="loginMode = 'password'">
            <KeyRound :size="16" />
            密码
          </button>
        </div>

        <label class="field">
          <span>邮箱</span>
          <input v-model="email" type="email" placeholder="user@example.com" />
        </label>

        <label v-if="pageMode === 'register' || loginMode === 'code'" class="field">
          <span>验证码</span>
          <div class="inline-input">
            <input v-model="code" inputmode="numeric" maxlength="6" placeholder="6 位验证码" />
            <button type="button" :disabled="loading" @click="sendCode">获取</button>
          </div>
        </label>

        <label v-if="pageMode === 'register' || loginMode === 'password'" class="field">
          <span>密码</span>
          <input v-model="password" type="password" placeholder="至少 8 位，包含字母和数字" />
        </label>

        <p class="form-note">{{ notice }}</p>
        <button class="primary-button" type="button" :disabled="!canSubmit || loading" @click="submit">
          {{ pageMode === 'register' ? '注册并进入' : '登录' }}
        </button>
      </div>
    </section>
  </main>
</template>
