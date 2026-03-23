<template>
  <div class="device-list">
    <h2>设备列表</h2>
    
    <!-- 搜索框 -->
    <el-card class="search-card" style="margin-bottom: 20px;">
      <el-form :inline="true" class="search-form">
        <el-form-item label="搜索设备">
          <el-input v-model="searchKeyword" placeholder="输入设备名称或ID" style="width: 300px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="searchDevices">搜索</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 设备表格 -->
    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span>设备管理</span>
        </div>
      </template>
      <el-table :data="pagedDevices" style="width: 100%">
        <el-table-column prop="device_id" label="设备ID" width="120" />
        <el-table-column prop="name" label="设备名称" />
        <el-table-column prop="location" label="位置" />
        <el-table-column label="负责人" width="100">
          <template #default="scope">
            {{ scope.row.负责人 || '未知' }}
          </template>
        </el-table-column>
        <el-table-column label="联系方式" width="150">
          <template #default="scope">
            {{ scope.row.联系方式 || '未知' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="400">
          <template #default="scope">
            <div class="operation-buttons">
              <el-button type="primary" size="small" @click="editDevice(scope.row)">编辑</el-button>
              <el-button type="success" size="small" @click="viewRealtimeData(scope.row.device_id)">实时数据</el-button>
              <el-button type="warning" size="small" @click="viewHistoryData(scope.row.device_id)">历史数据</el-button>
              <el-button type="danger" size="small" @click="viewWarningRecords(scope.row.device_id)">预警记录</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页组件 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="filteredDevices.length"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 编辑设备对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="编辑设备"
      width="500px"
    >
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="设备ID">
          <el-input v-model="editForm.device_id" disabled />
        </el-form-item>
        <el-form-item label="设备名称">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="位置">
          <el-input v-model="editForm.location" />
        </el-form-item>
        <el-form-item label="负责人">
          <el-input v-model="editForm.负责人" />
        </el-form-item>
        <el-form-item label="联系方式">
          <el-input v-model="editForm.联系方式" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveDevice">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'DeviceList',
  data() {
    return {
      devices: [],
      searchKeyword: '',
      dialogVisible: false,
      editForm: {
        device_id: '',
        name: '',
        location: '',
        负责人: '',
        联系方式: ''
      },
      currentPage: 1,
      pageSize: 10
    }
  },
  mounted() {
    this.loadDevices()
  },
  computed: {
    filteredDevices() {
      if (!this.searchKeyword) {
        return this.devices
      }
      return this.devices.filter(device => 
        device.name.includes(this.searchKeyword) || 
        device.device_id.includes(this.searchKeyword)
      )
    },
    pagedDevices() {
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      return this.filteredDevices.slice(start, end)
    }
  },
  methods: {
    searchDevices() {
      // 这里可以添加实际的搜索逻辑
      this.currentPage = 1 // 搜索后重置到第一页
    },
    editDevice(device) {
      // 编辑设备逻辑
      this.editForm = { ...device }
      this.dialogVisible = true
    },
    async saveDevice() {
      try {
        // 调用后端 API 更新设备信息
        const response = await axios.put(`/device/${this.editForm.device_id}`, {
          name: this.editForm.name,
          location: this.editForm.location,
          负责人: this.editForm.负责人,
          联系方式: this.editForm.联系方式
        })
        
        // 更新本地设备列表
        const index = this.devices.findIndex(item => item.device_id === this.editForm.device_id)
        if (index !== -1) {
          this.devices[index] = { ...this.editForm }
        }
        
        this.$message.success('设备信息已更新')
        this.dialogVisible = false
      } catch (error) {
        console.error('更新设备信息失败:', error)
        this.$message.error('更新设备信息失败，请重试')
      }
    },
    viewRealtimeData(deviceId) {
      // 跳转到实时数据页面，带上设备ID参数
      this.$router.push(`/dashboard/${deviceId}`)
    },
    viewHistoryData(deviceId) {
      // 跳转到历史数据页面，带上设备ID参数
      this.$router.push(`/history/${deviceId}`)
    },
    viewWarningRecords(deviceId) {
      // 跳转到预警记录页面，带上设备ID参数
      this.$router.push(`/warning/${deviceId}`)
    },
    handleSizeChange(val) {
      this.pageSize = val
      this.currentPage = 1 // 改变每页条数后重置到第一页
    },
    handleCurrentChange(val) {
      this.currentPage = val
    },
    async loadDevices() {
      try {
        const response = await axios.get('/device/list', {
          params: {
            page: 1,
            page_size: 10
          }
        })
        // 确保 response.data.devices 是一个数组
        this.devices = Array.isArray(response.data.devices) ? response.data.devices : []
      } catch (error) {
        console.error('获取设备列表失败:', error)
        // 发生错误时，设置默认值，确保页面不会空白
        this.devices = []
      }
    }
  }
}
</script>

<style scoped>
.device-list {
  padding: 0;
}

.search-form {
  margin-bottom: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.operation-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
