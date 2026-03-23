<template>
  <div class="device-threshold-config">
    <h2>设备阈值配置</h2>
    
    <!-- 批量设置按钮 -->
    <div style="margin-bottom: 20px; text-align: right;">
      <el-button
        type="success"
        @click="syncDevices"
        :loading="syncing"
      >
        设备更新
      </el-button>
      <el-button
        type="primary"
        @click="openBatchConfigDialog"
        :disabled="selectedDevices.length === 0"
        style="margin-left: 10px;"
      >
        批量设置
      </el-button>
      <span v-if="selectedDevices.length > 0" style="margin-left: 10px; color: #409EFF;">
        已选择 {{ selectedDevices.length }} 个设备
      </span>
    </div>
    
    <!-- 全设备展示 -->
    <el-card class="config-card">
      <template #header>
        <div class="card-header">
          <span>设备阈值列表</span>
        </div>
      </template>
      <el-table 
        :data="pagedDevices" 
        style="width: 100%"
        ref="deviceTable"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="设备名称" width="180" />
        <el-table-column prop="location" label="位置" width="180" />
        <el-table-column label="压力阈值 (MPa)">
          <template #default="scope">
            <el-input-number 
              v-model="scope.row.pressure_threshold" 
              :min="0" 
              :step="0.1" 
              @change="updateDeviceThreshold(scope.row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="流量阈值 (m³/h)">
          <template #default="scope">
            <el-input-number 
              v-model="scope.row.flow_threshold" 
              :min="0" 
              :step="0.5" 
              @change="updateDeviceThreshold(scope.row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="温度阈值 (°C)">
          <template #default="scope">
            <el-input-number 
              v-model="scope.row.temperature_threshold" 
              :min="0" 
              :step="1" 
              @change="updateDeviceThreshold(scope.row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button size="small" type="primary" @click="saveSingleDevice(scope.row)">
              保存
            </el-button>
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
          :total="devices.length"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
    
    <!-- 批量配置对话框 -->
    <el-dialog
      v-model="batchConfigDialogVisible"
      title="批量配置"
      width="500px"
    >
      <el-form :model="batchForm" label-width="120px">
        <el-form-item label="压力阈值 (MPa)">
          <el-input-number v-model="batchForm.pressure_threshold" :min="0" :step="0.1" />
        </el-form-item>
        <el-form-item label="流量阈值 (m³/h)">
          <el-input-number v-model="batchForm.flow_threshold" :min="0" :step="0.5" />
        </el-form-item>
        <el-form-item label="温度阈值 (°C)">
          <el-input-number v-model="batchForm.temperature_threshold" :min="0" :step="1" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="batchConfigDialogVisible = false">取消</el-button>
          <el-button type="info" @click="loadSmartDefaults">加载智能默认值</el-button>
          <el-button type="primary" @click="applyBatchConfig">应用到选中设备</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'DeviceThresholdConfig',
  data() {
    return {
      devices: [],
      syncing: false,
      batchForm: {
        pressure_threshold: 2.0,
        flow_threshold: 5.0,
        temperature_threshold: 80.0
      },
      selectedDevices: [],
      batchConfigDialogVisible: false,
      currentPage: 1,
      pageSize: 10
    }
  },
  computed: {
    pagedDevices() {
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      return this.devices.slice(start, end)
    }
  },
  mounted() {
    this.loadDevices()
  },
  methods: {
    async loadDevices() {
      try {
        const response = await axios.get('/device/list', {
          params: { page: 1, page_size: 100 }
        })
        this.devices = Array.isArray(response.data.devices) ? response.data.devices : []
      } catch (error) {
        console.error('获取设备列表失败:', error)
        this.devices = []
      }
    },
    async syncDevices() {
      this.syncing = true
      try {
        const response = await axios.get('/device/list', {
          params: { page: 1, page_size: 100 }
        })
        this.devices = Array.isArray(response.data.devices) ? response.data.devices : []
        this.$message.success(`设备同步成功，共 ${this.devices.length} 台设备`)
      } catch (error) {
        console.error('设备同步失败:', error)
        this.$message.error('设备同步失败')
      } finally {
        this.syncing = false
      }
    },
    async updateDeviceThreshold(device) {
      // 实时更新设备阈值
      console.log('更新设备阈值:', device)
    },
    async saveSingleDevice(device) {
      try {
        await axios.put(`/device/threshold/${device.device_id}`, {
          pressure_threshold: device.pressure_threshold,
          flow_threshold: device.flow_threshold,
          temperature_threshold: device.temperature_threshold
        })
        this.$message.success(`设备 ${device.name} 阈值保存成功`)
      } catch (error) {
        console.error('保存设备阈值失败:', error)
        this.$message.error('保存失败')
      }
    },
    async applyBatchConfig() {
      if (this.selectedDevices.length === 0) {
        this.$message.warning('请选择要配置的设备')
        return
      }
      
      try {
        const promises = this.selectedDevices.map(device => {
          return axios.put(`/device/threshold/${device.device_id}`, {
            pressure_threshold: this.batchForm.pressure_threshold,
            flow_threshold: this.batchForm.flow_threshold,
            temperature_threshold: this.batchForm.temperature_threshold
          })
        })
        
        await Promise.all(promises)
        this.$message.success(`批量配置应用成功，共配置 ${this.selectedDevices.length} 个设备`)
        this.loadDevices() // 刷新设备列表
        this.selectedDevices = [] // 清空选择
        this.batchConfigDialogVisible = false // 关闭对话框
      } catch (error) {
        console.error('批量配置失败:', error)
        this.$message.error('批量配置失败')
      }
    },
    async loadSmartDefaults() {
      try {
        const response = await axios.get('/data/smart-thresholds')
        if (response.data.success) {
          this.batchForm = { ...response.data.thresholds }
          this.$message.success('智能默认值加载成功')
        } else {
          this.$message.error('加载智能默认值失败')
        }
      } catch (error) {
        console.error('加载智能默认值失败:', error)
        this.$message.error('加载智能默认值失败')
      }
    },
    handleSelectionChange(selection) {
      this.selectedDevices = selection
    },
    openBatchConfigDialog() {
      if (this.selectedDevices.length === 0) {
        this.$message.warning('请选择要配置的设备')
        return
      }
      this.batchConfigDialogVisible = true
    },
    handleSizeChange(val) {
      this.pageSize = val
      this.currentPage = 1 // 改变每页条数后重置到第一页
    },
    handleCurrentChange(val) {
      this.currentPage = val
    }
  }
}
</script>

<style scoped>
.device-threshold-config {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.config-card {
  margin-bottom: 20px;
}

.el-table {
  margin-top: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>