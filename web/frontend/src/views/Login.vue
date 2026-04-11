<template>
  <div class="login-page">
    <!-- 动态背景 -->
    <div class="bg-orbs">
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="orb orb-3"></div>
    </div>

    <!-- 登录卡片 -->
    <div class="login-card">
      <div class="login-brand">
        <div class="login-logo">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
          </svg>
        </div>
        <h1>WindField</h1>
        <p>微小型无人机智能风场测试评估系统</p>
      </div>

      <el-form :model="loginForm" :rules="rules" ref="loginFormRef" class="login-form">
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            size="large"
            @keyup.enter="handleLogin"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" :loading="loading" @click="handleLogin" class="login-btn">
            登 录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-hint">
        <span>演示账号：</span>
        <code>admin</code> / <code>admin123</code>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'
import { authApi } from '@/api/auth'

const router = useRouter()
const userStore = useUserStore()
const loginFormRef = ref(null)
const loading = ref(false)

const loginForm = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  const valid = await loginFormRef.value?.validate()
  if (!valid) return
  loading.value = true
  try {
    const res = await authApi.login(loginForm)
    userStore.setToken(res.access_token)
    userStore.setUser(res.user)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (error) {
    console.error('登录失败:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  width: 100%;
  height: 100vh;
  background: var(--bg-base);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

/* 动态光球背景 */
.bg-orbs {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.35;
}
.orb-1 {
  width: 500px; height: 500px;
  background: radial-gradient(circle, var(--accent), transparent 70%);
  top: -15%; left: -10%;
  animation: float-1 20s ease-in-out infinite;
}
.orb-2 {
  width: 400px; height: 400px;
  background: radial-gradient(circle, #8b5cf6, transparent 70%);
  bottom: -10%; right: -5%;
  animation: float-2 25s ease-in-out infinite;
}
.orb-3 {
  width: 300px; height: 300px;
  background: radial-gradient(circle, #22c55e, transparent 70%);
  top: 50%; left: 60%;
  animation: float-3 18s ease-in-out infinite;
  opacity: 0.2;
}

@keyframes float-1 {
  0%, 100% { transform: translate(0, 0); }
  33% { transform: translate(80px, 50px); }
  66% { transform: translate(-30px, 80px); }
}
@keyframes float-2 {
  0%, 100% { transform: translate(0, 0); }
  33% { transform: translate(-60px, -40px); }
  66% { transform: translate(40px, -70px); }
}
@keyframes float-3 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-80px, 40px); }
}

/* 登录卡片 */
.login-card {
  width: 380px;
  padding: 40px 36px;
  background: rgba(20, 25, 38, 0.8);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg), var(--shadow-glow);
  position: relative;
  z-index: 1;
  animation: fade-in 0.6s ease-out;
}

.login-brand {
  text-align: center;
  margin-bottom: 32px;
}
.login-logo {
  width: 48px;
  height: 48px;
  margin: 0 auto 16px;
  background: linear-gradient(135deg, var(--accent), var(--accent-dark));
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}
.login-logo svg {
  width: 26px;
  height: 26px;
}
.login-brand h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.5px;
  margin-bottom: 6px;
}
.login-brand p {
  font-size: 13px;
  color: var(--text-muted);
}

.login-form {
  margin-top: 8px;
}
.login-form .el-form-item {
  margin-bottom: 20px;
}

.login-btn {
  width: 100%;
  height: 44px !important;
  font-size: 15px !important;
  font-weight: 600 !important;
  border-radius: var(--radius-sm) !important;
  letter-spacing: 2px;
}

.login-hint {
  margin-top: 20px;
  text-align: center;
  font-size: 12px;
  color: var(--text-muted);
}
.login-hint code {
  background: rgba(14, 165, 233, 0.1);
  color: var(--accent-light);
  padding: 1px 6px;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 11px;
}
</style>
