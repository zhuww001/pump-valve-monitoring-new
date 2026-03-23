<template>
  <div class="warning">
    <h2 class="page-title">
      预警管理
      <span v-if="routeDeviceId" class="device-filter-tag">
        (设备: {{ routeDeviceId }})
        <el-button type="text" size="small" @click="clearDeviceFilter">清除筛选</el-button>
      </span>
    </h2>
    
    <!-- 预警列表 -->
    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span>预警记录列表</span>
        </div>
      </template>
      <div class="table-wrapper">
        <el-table 
          :data="pagedWarningList" 
          style="width: 100%"
          :fit="true"
          :header-cell-style="{ fontWeight: 'bold', fontSize: '13px' }"
          :cell-style="{ fontSize: '13px' }"
        >
          <el-table-column prop="id" label="ID" min-width="60" show-overflow-tooltip />
          <el-table-column prop="device_id" label="设备" min-width="100" show-overflow-tooltip />
          <el-table-column prop="warning_type" label="类型" min-width="80">
            <template #default="scope">
              <el-tag 
                :type="scope.row.warning_type === 'pressure' ? 'danger' : scope.row.warning_type === 'flow' ? 'warning' : 'info'"
                size="small"
              >
                {{ scope.row.warning_type === 'pressure' ? '压力' : scope.row.warning_type === 'flow' ? '流量' : '温度' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="warning_value" label="当前值" min-width="80">
            <template #default="scope">
              <span :class="{ 'warning-value': scope.row.status === 'unprocessed' }">
                {{ scope.row.warning_value }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="threshold" label="阈值" min-width="80" />
          <el-table-column prop="status" label="状态" min-width="80">
            <template #default="scope">
              <el-tag :type="scope.row.status === 'unprocessed' ? 'warning' : 'success'" size="small">
                {{ scope.row.status === 'unprocessed' ? '未处理' : '已处理' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="时间" min-width="140" show-overflow-tooltip>
            <template #default="scope">
              {{ formatDateTime(scope.row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="90" fixed="right">
            <template #default="scope">
              <el-button 
                type="primary" 
                size="small" 
                @click="handleWarning(scope.row)"
                :disabled="scope.row.status === 'processed'"
              >
                处理
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <!-- 分页组件 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
    
    <!-- 处理预警对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="处理预警"
      width="450px"
      :close-on-click-modal="false"
    >
      <el-form :model="warningForm" label-width="80px">
        <el-form-item label="预警ID">
          <el-input v-model="warningForm.id" disabled size="small" />
        </el-form-item>
        <el-form-item label="设备ID">
          <el-input v-model="warningForm.device_id" disabled size="small" />
        </el-form-item>
        <el-form-item label="预警类型">
          <el-input v-model="warningForm.warning_type" disabled size="small" />
        </el-form-item>
        <el-form-item label="预警值">
          <el-input v-model="warningForm.warning_value" disabled size="small" />
        </el-form-item>
        <el-form-item label="阈值">
          <el-input v-model="warningForm.threshold" disabled size="small" />
        </el-form-item>
        <el-form-item label="处理备注">
          <el-input type="textarea" v-model="warningForm.remark" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false" size="small">取消</el-button>
          <el-button type="primary" @click="submitWarning" size="small">提交</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Warning',
  data() {
    return {
      warningList: [],
      total: 0,
      dialogVisible: false,
      warningForm: {
        id: '',
        device_id: '',
        warning_type: '',
        warning_value: '',
        threshold: '',
        remark: ''
      },
      currentPage: 1,
      pageSize: 10
    }
  },
  computed: {
    pagedWarningList() {
      return this.warningList
    },
    routeDeviceId() {
      return this.$route.params.device_id
    }
  },
  mounted() {
    this.loadWarningList()
    // 定时更新预警列表
    this.interval = setInterval(() => {
      this.loadWarningList()
    }, 10000)
  },
  watch: {
    routeDeviceId: {
      handler() {
        this.currentPage = 1
        this.loadWarningList()
      },
      immediate: true
    }
  },
  beforeUnmount() {
    clearInterval(this.interval)
  },
  methods: {
    async loadWarningList() {
      try {
        const params = {
          page: this.currentPage,
          page_size: this.pageSize
        }
        if (this.routeDeviceId) {
          params.device_id = this.routeDeviceId
        }
        const response = await axios.get('/warning/list', { params })
        this.warningList = response.data.items
        this.total = response.data.total
      } catch (error) {
        console.error('获取预警列表失败:', error)
        this.warningList = []
        this.total = 0
      }
    },
    handleWarning(warning) {
      this.warningForm = {
        id: warning.id,
        device_id: warning.device_id,
        warning_type: warning.warning_type === 'pressure' ? '压力' : warning.warning_type === 'flow' ? '流量' : '温度',
        warning_value: warning.warning_value,
        threshold: warning.threshold,
        remark: ''
      }
      this.dialogVisible = true
    },
    async submitWarning() {
      try {
        await axios.put(`/warning/status/${this.warningForm.id}`, {
          status: 'processed'
        })
        this.$message.success('处理成功')
        this.dialogVisible = false
        this.loadWarningList()
      } catch (error) {
        console.error('处理预警失败:', error)
        this.$message.error('处理失败')
      }
    },
    handleSizeChange(val) {
      this.pageSize = val
      this.currentPage = 1 // 改变每页条数后重置到第一页
      this.loadWarningList()
    },
    handleCurrentChange(val) {
      this.currentPage = val
      this.loadWarningList()
    },
    clearDeviceFilter() {
      // 清除设备筛选，跳转到不带设备ID的预警页面
      this.$router.push('/warning')
    },
    formatDateTime(timestamp) {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      return date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      }).replace(/\//g, '-')
    }
  }
}
</script>

<style scoped>
.warning {
  padding: 0;
}

.page-title {
  margin: 0 0 15px 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.device-filter-tag {
  font-size: 14px;
  font-weight: normal;
  color: #409EFF;
  margin-left: 10px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.table-wrapper {
  width: 100%;
  overflow-x: auto;
}

.table-card {
  margin-bottom: 20px;
  overflow: visible;
}

.warning-value {
  color: #f56c6c;
  font-weight: 600;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  width: 100%;
  padding: 10px 0 0 0;
  box-sizing: border-box;
}

/* 响应式适配 */
@media screen and (max-width: 1366px) {
  .page-title {
    font-size: 16px;
  }
  
  .pagination-container {
    justify-content: center;
    flex-wrap: wrap;
  }
}

@media screen and (max-width: 768px) {
  .page-title {
    font-size: 14px;
  }
  
  .pagination-container {
    justify-content: center;
  }
  
  :deep(.el-pagination) {
    font-size: 12px;
  }
}
</style>
