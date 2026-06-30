<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { KeyRound, Mail, ShieldCheck } from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const mode = ref<'code' | 'password'>('code')
const email = ref('demo@example.com')
const code = ref('')
const password = ref('')
const notice = ref('演示验证码固定为 246810')

const canSubmit = computed(() => {
  if (!email.value.includes('@')) return false
  return mode.value === 'code' ? code.value.length === 6 : password.value.length >= 4
})

const sendCode = () => {
  const sent = auth.sendCode()
  code.value = sent
  notice.value = `验证码已填入：${sent}`
}

const submit = () => {
  if (!canSubmit.value) return
  auth.login(email.value)
  router.push({ name: 'home' })
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
          <button type="button" :class="{ active: mode === 'code' }" @click="mode = 'code'">
            <Mail :size="16" />
            验证码
          </button>
          <button type="button" :class="{ active: mode === 'password' }" @click="mode = 'password'">
            <KeyRound :size="16" />
            密码
          </button>
        </div>

        <label class="field">
          <span>邮箱</span>
          <input v-model="email" type="email" placeholder="user@example.com" />
        </label>

        <label v-if="mode === 'code'" class="field">
          <span>验证码</span>
          <div class="inline-input">
            <input v-model="code" inputmode="numeric" maxlength="6" placeholder="6 位验证码" />
            <button type="button" @click="sendCode">获取</button>
          </div>
        </label>

        <label v-else class="field">
          <span>密码</span>
          <input v-model="password" type="password" placeholder="输入任意 4 位以上密码" />
        </label>

        <p class="form-note">{{ notice }}</p>
        <button class="primary-button" type="button" :disabled="!canSubmit" @click="submit">登录 / 注册</button>
      </div>
    </section>
  </main>
</template>
