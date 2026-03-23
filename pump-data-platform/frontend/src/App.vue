<template>
  <div class="app-container">
    <!-- 登录页面 -->
    <template v-if="isLoginPage">
      <router-view />
    </template>
    
    <!-- 主应用页面 -->
    <template v-else>
      <el-container>
        <el-header height="60px" class="header">
          <div class="header-left">
            <el-button 
              class="collapse-btn"
              :icon="isCollapse ? Expand : Fold" 
              @click="toggleCollapse"
              text
              style="color: white; font-size: 20px; margin-right: 15px;"
            />
            <h1>泵阀管道堵塞预警系统</h1>
          </div>
          <div class="header-right">
            <el-dropdown>
              <span class="user-dropdown">
                <el-icon><i-ep-user /></el-icon>
                <span>{{ userName }}</span>
                <el-icon class="el-icon--right"><i-ep-arrow-down /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="handleLogout">
                    <el-icon><i-ep-switch-button /></el-icon>
                    <span>退出登录</span>
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>
        <el-container class="main-container">
          <el-aside :width="isCollapse ? '64px' : '200px'" class="aside">
            <el-menu
              :default-active="$route.path"
              :collapse="isCollapse"
              :collapse-transition="false"
              class="el-menu-vertical-demo"
              router
            >
              <el-menu-item index="/">
                <el-icon><i-ep-monitor /></el-icon>
                <template #title>实时监控</template>
              </el-menu-item>
              <el-menu-item index="/device-list">
                <el-icon><i-ep-list /></el-icon>
                <template #title>设备列表</template>
              </el-menu-item>
              <el-menu-item index="/history">
                <el-icon><i-ep-data-line /></el-icon>
                <template #title>历史数据</template>
              </el-menu-item>
              <el-menu-item index="/warning">
                <el-icon><i-ep-warning /></el-icon>
                <template #title>预警管理</template>
              </el-menu-item>
              <el-sub-menu index="/config">
                <template #title>
                  <el-icon><i-ep-setting /></el-icon>
                  <span>配置中心</span>
                </template>
                <el-menu-item index="/data-source-config">
                  <span>数据源配置</span>
                </el-menu-item>
                <el-menu-item index="/device-threshold-config">
                  <span>设备阈值配置</span>
                </el-menu-item>
              </el-sub-menu>
              <el-menu-item index="/gateway">
                <el-icon><i-ep-cpu /></el-icon>
                <template #title>边缘网关</template>
              </el-menu-item>
              <el-sub-menu index="/system">
                <template #title>
                  <el-icon><i-ep-tools /></el-icon>
                  <span>系统设置</span>
                </template>
                <el-menu-item index="/system/user">
                  <span>用户管理</span>
                </el-menu-item>
                <el-menu-item index="/system/role">
                  <span>角色管理</span>
                </el-menu-item>
                <el-menu-item index="/system/menu">
                  <span>菜单管理</span>
                </el-menu-item>
              </el-sub-menu>
            </el-menu>
          </el-aside>
          <el-main class="main">
            <router-view />
          </el-main>
        </el-container>
      </el-container>
    </template>
  </div>
</template>

<script>
import { Monitor, DataLine, Warning, Setting, List, Cpu, Tools, User, ArrowDown, SwitchButton, Fold, Expand } from '@element-plus/icons-vue'

export default {
  name: 'App',
  components: {
    'i-ep-monitor': Monitor,
    'i-ep-data-line': DataLine,
    'i-ep-warning': Warning,
    'i-ep-setting': Setting,
    'i-ep-list': List,
    'i-ep-cpu': Cpu,
    'i-ep-tools': Tools,
    'i-ep-user': User,
    'i-ep-arrow-down': ArrowDown,
    'i-ep-switch-button': SwitchButton
  },
  data() {
    return {
      isCollapse: false,
      Fold: Fold,
      Expand: Expand
    }
  },
  computed: {
    userName() {
      const user = localStorage.getItem('user')
      console.log('读取用户信息:', user)
      if (user) {
        try {
          const parsedUser = JSON.parse(user)
          console.log('解析后的用户信息:', parsedUser)
          return parsedUser.username
        } catch (e) {
          console.error('解析用户信息失败:', e)
          return ''
        }
      }
      return ''
    },
    isLoginPage() {
      return this.$route.path === '/login'
    }
  },
  mounted() {
    // 根据屏幕宽度自动折叠侧边栏
    this.checkScreenWidth()
    window.addEventListener('resize', this.checkScreenWidth)
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.checkScreenWidth)
  },
  methods: {
    toggleCollapse() {
      this.isCollapse = !this.isCollapse
    },
    checkScreenWidth() {
      // 在1366px以下屏幕自动折叠侧边栏
      this.isCollapse = window.innerWidth < 1366
    },
    handleLogout() {
      this.$confirm('确定要退出登录吗？', '警告', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        // 清除本地存储的token和用户信息
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        // 跳转到登录页
        this.$router.push('/login')
      }).catch(() => {})
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  width: 100%;
  overflow: hidden;
}

.app-container {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.header {
  background-color: #409EFF;
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-left h1 {
  margin: 0;
  font-size: 18px;
  white-space: nowrap;
}

.collapse-btn {
  padding: 8px;
  margin-right: 10px;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-dropdown {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 4px;
  transition: all 0.3s;
  color: white;
}

.user-dropdown:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.user-dropdown i {
  margin-right: 8px;
}

.el-icon--right {
  margin-left: 4px;
}

.main-container {
  height: calc(100vh - 60px);
  overflow: hidden;
}

.aside {
  background-color: #f5f7fa;
  border-right: 1px solid #e4e7ed;
  transition: width 0.3s;
  overflow-x: hidden;
}

.main {
  padding: 15px;
  overflow-y: auto;
  background-color: #f0f2f5;
  min-width: 0;
}

.el-menu-vertical-demo:not(.el-menu--collapse) {
  width: 200px;
}

.el-menu-vertical-demo {
  border-right: none;
}

/* 响应式适配 */
@media screen and (max-width: 1366px) {
  .header-left h1 {
    font-size: 16px;
  }
  
  .main {
    padding: 10px;
  }
}

@media screen and (max-width: 1280px) {
  .header-left h1 {
    font-size: 14px;
  }
}

@media screen and (max-width: 768px) {
  .header-left h1 {
    font-size: 14px;
  }
  
  .user-dropdown span {
    display: none;
  }
}
</style>
