import request from './index'

export const authApi = {
  // 登录
  login(data) {
    return request.post('/auth/login', data)
  },

  // 登出
  logout() {
    return request.post('/auth/logout')
  },

  // 获取用户信息
  getProfile() {
    return request.get('/auth/profile')
  }
}
