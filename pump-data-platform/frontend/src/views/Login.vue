<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="login-header">
          <h2>泵阀管道堵塞预警系统</h2>
          <p>请登录系统</p>
        </div>
      </template>
      <el-form :model="loginForm" :rules="rules" ref="loginFormRef" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="loginForm.username" placeholder="请输入用户名" prefix-icon="el-icon-user" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" prefix-icon="el-icon-lock" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleLogin" :loading="loading" style="width: 100%">
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Login',
  data() {
    return {
      loginForm: {
        username: '',
        password: ''
      },
      rules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' }
        ]
      },
      loading: false
    }
  },
  methods: {
    async handleLogin() {
      const valid = await this.$refs.loginFormRef.validate()
      if (!valid) return
      
      this.loading = true
      try {
        // 调用后端登录API
        const response = await axios.post('/auth/login', this.loginForm)
        
        // 清除旧的用户信息
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        
        // 存储新的token和用户信息
        const token = response.data.access_token
        const user = response.data.user
        localStorage.setItem('token', token)
        localStorage.setItem('user', JSON.stringify(user))
        
        console.log('登录成功，存储token:', token)
        console.log('登录成功，存储用户信息:', user)
        console.log('localStorage中的token:', localStorage.getItem('token'))
        console.log('localStorage中的user:', localStorage.getItem('user'))
        
        this.$message.success('登录成功')
        
        // 使用setTimeout确保数据已存储后再跳转
        setTimeout(() => {
          this.$router.push('/').catch(err => {
            console.error('路由跳转失败:', err)
          })
        }, 100)
      } catch (error) {
        console.error('登录失败:', error)
        if (error.response && error.response.data) {
          this.$message.error(error.response.data.detail || '登录失败，请稍后重试')
        } else {
          this.$message.error('登录失败，请稍后重试')
        }
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  border-radius: 10px;
  overflow: hidden;
}

.login-header {
  text-align: center;
  margin-bottom: 20px;
}

.login-header h2 {
  margin: 0 0 10px 0;
  color: #303133;
}

.login-header p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.el-form {
  padding: 0 20px 20px;
}
</style>
