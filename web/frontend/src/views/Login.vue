<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h1>微小型无人机智能风场测试评估系统</h1>
        <p>Web数字孪生平台</p>
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
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleLogin"
            style="width: 100%"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-tips">
        <p>默认账号：</p>
        <p>管理员: admin / admin123</p>
        <p>操作员: operator / operator123</p>
        <p>观察员: viewer / viewer123</p>
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

const loginForm = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  const valid = await loginFormRef.value?.validate()
  if (!valid) return

  loading.value = true

  try {
    const res = await authApi.login(loginForm)

    // 保存token和用户信息
    userStore.setToken(res.access_token)
    userStore.setUser(res.user)

    ElMessage.success('登录成功')

    // 跳转到首页
    router.push('/')
  } catch (error) {
    console.error('登录失败:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  width: 100%;
  height: 100vh;
  background: linear-gradient(135deg, #1a1c23 0%, #2a2c33 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-box {
  width: 400px;
  padding: 40px;
  background: rgba(42, 44, 51, 0.9);
  border: 1px solid #3a3c43;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  font-size: 22px;
  color: #e1e1e6;
  margin-bottom: 8px;
}

.login-header p {
  font-size: 14px;
  color: #8a8f98;
}

.login-form {
  margin-top: 24px;
}

.login-tips {
  margin-top: 24px;
  padding: 16px;
  background: rgba(58, 60, 67, 0.5);
  border-radius: 6px;
  font-size: 12px;
  color: #8a8f98;
  line-height: 1.8;
}

.login-tips p {
  margin: 0;
}
</style>
