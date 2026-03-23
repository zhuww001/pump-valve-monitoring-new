<template>
  <div class="dashboard">
    <h2 class="page-title">实时监控</h2>
    
    <!-- 数据趋势图表 -->
    <el-card class="chart-card">
      <template #header>
        <div class="chart-header">
          <span>数据趋势</span>
          <el-select v-model="selectedDevice" placeholder="选择设备" size="small" v-if="!routeDeviceId" @change="updateChart">
            <el-option
              v-for="device in allDevices"
              :key="device.device_id"
              :label="device.name"
              :value="device.device_id"
            />
          </el-select>
        </div>
      </template>
      <div class="chart-container">
        <div ref="pressureChartRef" class="single-chart"></div>
        <div ref="flowChartRef" class="single-chart"></div>
        <div ref="temperatureChartRef" class="single-chart"></div>
      </div>
    </el-card>
    
    <!-- 设备状态卡片 -->
    <div class="device-section">
      <div class="section-header">
        <span>实时数据</span>
      </div>
      <el-row :gutter="15" class="device-row">
        <el-col 
          :xs="24" 
          :sm="12" 
          :md="8" 
          :lg="8" 
          :xl="6" 
          v-for="device in pagedDevices" 
          :key="device.device_id"
          class="device-col"
        >
          <el-card :body-style="{ padding: '15px' }" :class="{ 'warning-card': device.status === 'warning' }">
            <template #header>
              <div class="card-header">
                <span class="device-name">{{ device.name }}</span>
                <div class="tag-group">
                  <el-tag size="small" type="info" v-if="device.realtime_data?.source_type === 'edge_gateway'">边缘</el-tag>
                  <el-tag size="small" type="success" v-else-if="device.realtime_data?.source_type === 'simulate'">模拟</el-tag>
                  <el-tag :type="device.status === 'normal' ? 'success' : 'warning'" size="small">
                    {{ device.status === 'normal' ? '正常' : '预警' }}
                  </el-tag>
                </div>
              </div>
            </template>
            <div class="card-body">
              <div class="data-row">
                <div class="data-item">
                  <span class="label">位置</span>
                  <span class="value">{{ device.location }}</span>
                </div>
              </div>
              <div class="data-row metrics">
                <div class="metric-item">
                  <span class="metric-label">压力</span>
                  <span class="metric-value">{{ device.realtime_data?.pressure || 0 }}</span>
                  <span class="metric-unit">MPa</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">流量</span>
                  <span class="metric-value">{{ device.realtime_data?.flow || 0 }}</span>
                  <span class="metric-unit">m³/h</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">温度</span>
                  <span class="metric-value">{{ device.realtime_data?.temperature || 0 }}</span>
                  <span class="metric-unit">°C</span>
                </div>
              </div>
              <div class="data-row update-time">
                <span class="label">更新</span>
                <span class="value time">{{ formatDateTime(device.realtime_data?.timestamp) || '无数据' }}</span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <!-- 分页控件 -->
      <div class="pagination-container" v-if="total > 0">
        <el-pagination
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          :current-page="currentPage"
          :page-sizes="[3, 6, 9, 12]"
          :page-size="pageSize"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
        />
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import * as echarts from 'echarts'

export default {
  name: 'Dashboard',
  data() {
    return {
      devices: [],
      allDevices: [],
      selectedDevice: '',
      pressureChart: null,
      flowChart: null,
      temperatureChart: null,
      currentPage: 1,
      pageSize: 3,
      total: 0
    }
  },
  computed: {
    routeDeviceId() {
      return this.$route.params.device_id
    },
    pagedDevices() {
      return this.devices
    },
    // total 现在是从后端返回的，不需要计算
    // total() {
    //   return this.devices.length
    // }
  },
  mounted() {
    this.loadAllDevices()
    this.loadDevices()
    this.initChart()
    this.interval = setInterval(() => {
      this.loadDevices()
      this.updateChart()
    }, 5000)
  },
  beforeUnmount() {
    clearInterval(this.interval)
    if (this.pressureChart) {
      this.pressureChart.dispose()
    }
    if (this.flowChart) {
      this.flowChart.dispose()
    }
    if (this.temperatureChart) {
      this.temperatureChart.dispose()
    }
  },
  methods: {
    async loadDevices() {
      try {
        if (this.routeDeviceId) {
          const device = (await axios.get(`/device/${this.routeDeviceId}`)).data
          try {
            device.realtime_data = (await axios.get(`/data/realtime/${device.device_id}`)).data
          } catch (error) {
            console.error(`获取设备 ${device.name} 实时数据失败:`, error)
          }
          this.devices = [device]
          this.total = 1
          this.selectedDevice = device.device_id
          this.updateChart()
        } else {
          const response = (await axios.get('/device/list', {
            params: {
              page: this.currentPage,
              page_size: this.pageSize
            }
          })).data
          // 确保 response.devices 是一个数组
          const devices = Array.isArray(response.devices) ? response.devices : []
          // 并行获取所有设备实时数据
          await Promise.all(
            devices.map(async (device) => {
              try {
                device.realtime_data = (await axios.get(`/data/realtime/${device.device_id}`)).data
              } catch (error) {
                console.error(`获取设备 ${device.name} 实时数据失败:`, error)
              }
            })
          )
          this.devices = devices
          this.total = response.total || 0
          if (devices.length > 0 && !this.selectedDevice) {
            this.selectedDevice = devices[0].device_id
            this.updateChart()
          }
        }
      } catch (error) {
        console.error('获取设备列表失败:', error)
        // 发生错误时，设置默认值，确保页面不会空白
        this.devices = []
        this.total = 0
      }
    },
    initChart() {
      // 初始化压力图表
      this.pressureChart = echarts.init(this.$refs.pressureChartRef)
      this.pressureChart.setOption({
        title: {
          text: '压力趋势',
          textStyle: {
            fontSize: 14
          }
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross',
            label: {
              backgroundColor: '#6a7985'
            }
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '50px',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: []
        },
        yAxis: {
          type: 'value',
          name: '压力(MPa)',
          nameTextStyle: {
            fontSize: 11
          },
          position: 'left',
          axisLine: {
            show: true,
            lineStyle: {
              color: '#5470c6'
            }
          },
          axisLabel: {
            formatter: '{value}'
          }
        },
        series: [
          {
            name: '压力',
            type: 'line',
            data: [],
            lineStyle: {
              color: '#5470c6'
            },
            itemStyle: {
              color: '#5470c6'
            }
          }
        ]
      })

      // 初始化流量图表
      this.flowChart = echarts.init(this.$refs.flowChartRef)
      this.flowChart.setOption({
        title: {
          text: '流量趋势',
          textStyle: {
            fontSize: 14
          }
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross',
            label: {
              backgroundColor: '#6a7985'
            }
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '50px',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: []
        },
        yAxis: {
          type: 'value',
          name: '流量(m³/h)',
          nameTextStyle: {
            fontSize: 11
          },
          position: 'left',
          axisLine: {
            show: true,
            lineStyle: {
              color: '#91cc75'
            }
          },
          axisLabel: {
            formatter: '{value}'
          }
        },
        series: [
          {
            name: '流量',
            type: 'line',
            data: [],
            lineStyle: {
              color: '#91cc75'
            },
            itemStyle: {
              color: '#91cc75'
            }
          }
        ]
      })

      // 初始化温度图表
      this.temperatureChart = echarts.init(this.$refs.temperatureChartRef)
      this.temperatureChart.setOption({
        title: {
          text: '温度趋势',
          textStyle: {
            fontSize: 14
          }
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross',
            label: {
              backgroundColor: '#6a7985'
            }
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '50px',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: []
        },
        yAxis: {
          type: 'value',
          name: '温度(°C)',
          nameTextStyle: {
            fontSize: 11
          },
          position: 'left',
          axisLine: {
            show: true,
            lineStyle: {
              color: '#fac858'
            }
          },
          axisLabel: {
            formatter: '{value}'
          }
        },
        series: [
          {
            name: '温度',
            type: 'line',
            data: [],
            lineStyle: {
              color: '#fac858'
            },
            itemStyle: {
              color: '#fac858'
            }
          }
        ]
      })
      
      // 监听窗口大小变化
      window.addEventListener('resize', this.handleResize)
    },
    handleResize() {
      if (this.pressureChart) {
        this.pressureChart.resize()
      }
      if (this.flowChart) {
        this.flowChart.resize()
      }
      if (this.temperatureChart) {
        this.temperatureChart.resize()
      }
    },
    formatLocalISO(date) {
      const pad = n => String(n).padStart(2, '0')
      return `${date.getFullYear()}-${pad(date.getMonth()+1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
    },
    async updateChart() {
      if (!this.selectedDevice) return

      try {
        const now = new Date()
        const start = new Date(now.getTime() - 3600000) // 1小时前

        const response = await axios.get(`/data/history/${this.selectedDevice}`, {
          params: {
            start_time: this.formatLocalISO(start),
            end_time: this.formatLocalISO(now)
          }
        })

        const data = response.data
        const timestamps = data.map(item => {
          // 后端返回本地时间字符串，直接截取时:分
          const ts = item.timestamp
          return ts.length >= 16 ? ts.slice(11, 16) : ts
        })
        const pressure = data.map(item => item.pressure)
        const flow = data.map(item => item.flow)
        const temperature = data.map(item => item.temperature)
        
        // 更新压力图表
        if (this.pressureChart) {
          this.pressureChart.setOption({
            xAxis: {
              data: timestamps
            },
            series: [
              {
                name: '压力',
                data: pressure
              }
            ]
          })
        }

        // 更新流量图表
        if (this.flowChart) {
          this.flowChart.setOption({
            xAxis: {
              data: timestamps
            },
            series: [
              {
                name: '流量',
                data: flow
              }
            ]
          })
        }

        // 更新温度图表
        if (this.temperatureChart) {
          this.temperatureChart.setOption({
            xAxis: {
              data: timestamps
            },
            series: [
              {
                name: '温度',
                data: temperature
              }
            ]
          })
        }
      } catch (error) {
        console.error('更新图表失败:', error)
      }
    },
    handleSizeChange(val) {
      this.pageSize = val
      this.currentPage = 1
      this.loadDevices()
    },
    handleCurrentChange(val) {
      this.currentPage = val
      this.loadDevices()
    },
    formatDateTime(timestamp) {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      const now = new Date()
      const diff = now - date
      
      // 如果是今天，只显示时间
      if (diff < 24 * 60 * 60 * 1000 && date.getDate() === now.getDate()) {
        return date.toLocaleTimeString('zh-CN', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false
        })
      }
      
      return date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      }).replace(/\//g, '-')
    },
    async loadAllDevices() {
      try {
        const response = await axios.get('/device/list', {
          params: {
            page: 1,
            page_size: 100 // 加载足够多的设备
          }
        })
        // 确保 response.devices 是一个数组
        this.allDevices = Array.isArray(response.data.devices) ? response.data.devices : []
      } catch (error) {
        console.error('获取所有设备失败:', error)
        this.allDevices = []
      }
    }
  }
}
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.page-title {
  margin: 0 0 15px 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.device-row {
  margin-bottom: 0 !important;
}

.device-col {
  margin-bottom: 15px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.device-name {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
}

.tag-group {
  display: flex;
  gap: 5px;
  align-items: center;
}

.card-body {
  padding: 0;
}

.data-row {
  margin-bottom: 10px;
}

.data-row:last-child {
  margin-bottom: 0;
}

.data-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.label {
  font-size: 13px;
  color: #909399;
}

.value {
  font-size: 13px;
  color: #606266;
}

.value.time {
  font-size: 12px;
  color: #909399;
}

.metrics {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-top: 1px solid #ebeef5;
  border-bottom: 1px solid #ebeef5;
  margin: 10px 0;
}

.metric-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.metric-label {
  font-size: 11px;
  color: #909399;
  margin-bottom: 4px;
}

.metric-value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  line-height: 1.2;
}

.metric-unit {
  font-size: 10px;
  color: #c0c4cc;
  margin-top: 2px;
}

.update-time {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 8px;
}

.warning-card {
  border-color: #e6a23c;
  background-color: #fdf6ec;
}

.warning-card :deep(.el-card__header) {
  background-color: #fdf6ec;
  border-bottom-color: #f5dab1;
}

.chart-card {
  margin-bottom: 15px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.single-chart {
  width: 100%;
  height: 300px;
}

.device-section {
  margin-top: 15px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.section-header span {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

/* 响应式适配 */
@media screen and (max-width: 1366px) {
  .single-chart {
    height: 250px;
  }
  
  .metric-value {
    font-size: 16px;
  }
}

@media screen and (max-width: 1280px) {
  .single-chart {
    height: 230px;
  }
  
  .page-title {
    font-size: 16px;
  }
}

@media screen and (max-width: 768px) {
  .single-chart {
    height: 200px;
  }
  
  .metrics {
    flex-direction: row;
  }
  
  .metric-value {
    font-size: 14px;
  }
}
</style>
