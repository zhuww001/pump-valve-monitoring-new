<template>
  <div class="data-source-config">
    <h2>数据源配置</h2>
    
    <el-card class="config-card">
      <template #header>
        <div class="card-header">
          <span>系统级数据源配置</span>
        </div>
      </template>
      <el-form :model="dataSourceForm" label-width="120px">
        <el-form-item label="数据源类型">
          <el-radio-group v-model="dataSourceForm.type" @change="handleDataSourceChange">
            <el-radio label="simulate">模拟数据源</el-radio>
            <el-radio label="api">API数据源</el-radio>
            <el-radio label="report">设备上报数据源</el-radio>
            <el-radio label="mqtt">MQTT数据源</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <!-- API数据源配置 -->
        <el-collapse v-if="dataSourceForm.type === 'api'">
          <el-collapse-item title="API参数配置">
            <el-form-item label="API基础URL">
              <el-input v-model="dataSourceForm.config.api_base_url" placeholder="例如: http://localhost:8000" />
            </el-form-item>
            <el-form-item label="API Token">
              <el-input v-model="dataSourceForm.config.api_token" placeholder="API访问令牌" />
            </el-form-item>
            <el-form-item label="API端点">
              <el-input v-model="dataSourceForm.config.api_endpoint" placeholder="例如: /api/pump-data" />
            </el-form-item>
          </el-collapse-item>
        </el-collapse>
        
        <!-- MQTT数据源配置 -->
        <el-collapse v-if="dataSourceForm.type === 'mqtt'">
          <el-collapse-item title="MQTT参数配置">
            <el-form-item label="MQTT Broker">
              <el-input v-model="dataSourceForm.config.mqtt_broker" placeholder="例如: localhost" />
            </el-form-item>
            <el-form-item label="MQTT端口">
              <el-input v-model.number="dataSourceForm.config.mqtt_port" placeholder="例如: 1883" />
            </el-form-item>
            <el-form-item label="MQTT用户名">
              <el-input v-model="dataSourceForm.config.mqtt_username" placeholder="可选" />
            </el-form-item>
            <el-form-item label="MQTT密码">
              <el-input v-model="dataSourceForm.config.mqtt_password" type="password" placeholder="可选" />
            </el-form-item>
            <el-form-item label="MQTT主题">
              <el-input v-model="dataSourceForm.config.mqtt_topic" placeholder="例如: pump-valve/#" />
            </el-form-item>
            <el-form-item label="MQTT客户端ID">
              <el-input v-model="dataSourceForm.config.mqtt_client_id" placeholder="例如: pump-valve-monitor" />
            </el-form-item>
          </el-collapse-item>
        </el-collapse>
        
        <el-form-item>
          <el-button type="primary" @click="saveDataSourceConfig">保存配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'DataSourceConfig',
  data() {
    return {
      dataSourceForm: {
        type: 'simulate',
        config: {
          api_base_url: '',
          api_token: '',
          api_endpoint: '/api/pump-data',
          mqtt_broker: 'localhost',
          mqtt_port: 1883,
          mqtt_username: '',
          mqtt_password: '',
          mqtt_topic: 'pump-valve/#',
          mqtt_client_id: 'pump-valve-monitor'
        }
      }
    }
  },
  mounted() {
    this.loadCurrentDataSource()
  },
  methods: {
    async loadCurrentDataSource() {
      try {
        const response = await axios.get('/data-source/current')
        this.dataSourceForm.type = response.data.type
        // 确保配置对象包含所有必要的字段
        this.dataSourceForm.config = {
          // 默认值
          api_base_url: '',
          api_token: '',
          api_endpoint: '/api/pump-data',
          mqtt_broker: 'localhost',
          mqtt_port: 1883,
          mqtt_username: '',
          mqtt_password: '',
          mqtt_topic: 'pump-valve/#',
          mqtt_client_id: 'pump-valve-monitor',
          // 从响应中覆盖
          ...response.data.config
        }
      } catch (error) {
        console.error('获取数据源配置失败:', error)
      }
    },
    handleDataSourceChange() {
      // 切换数据源类型时的处理
    },
    async saveDataSourceConfig() {
      try {
        await axios.post('/data-source/switch', {
          type: this.dataSourceForm.type,
          config: this.dataSourceForm.config
        })
        this.$message.success('数据源配置保存成功')
      } catch (error) {
        console.error('保存数据源配置失败:', error)
        this.$message.error('保存失败')
      }
    }
  }
}
</script>

<style scoped>
.data-source-config {
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
</style>