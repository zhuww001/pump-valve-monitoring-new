<template>
  <div class="history">
    <h2 class="page-title">
      历史数据
      <span v-if="routeDeviceId" class="device-filter-tag">
        (设备: {{ routeDeviceId }})
        <el-button type="text" size="small" @click="clearDeviceFilter">清除筛选</el-button>
      </span>
    </h2>
    
    <!-- 筛选条件 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="设备">
          <el-select v-model="filterForm.device_id" placeholder="请选择设备" style="width:160px" @change="handleDeviceChange">
            <el-option
              v-for="d in devices"
              :key="d.device_id"
              :label="d.name"
              :value="d.device_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-radio-group v-model="timeRange" @change="handleTimeRangeChange">
            <el-radio-button label="1h">1小时</el-radio-button>
            <el-radio-button label="24h">24小时</el-radio-button>
            <el-radio-button label="72h">72小时</el-radio-button>
            <el-radio-button label="custom">自定义</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="开始时间" v-if="timeRange === 'custom'">
          <el-date-picker
            v-model="filterForm.start_time"
            type="datetime"
            placeholder="选择开始时间"
            style="width: 200px"
            @change="loadHistoryData"
          />
        </el-form-item>
        <el-form-item label="结束时间" v-if="timeRange === 'custom'">
          <el-date-picker
            v-model="filterForm.end_time"
            type="datetime"
            placeholder="选择结束时间"
            style="width: 200px"
            @change="loadHistoryData"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadHistoryData">查询</el-button>
          <el-button @click="exportData">导出</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- Tab页 -->
    <el-card style="margin-top: 20px;">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="趋势图" name="chart">
          <!-- 数据趋势图表 -->
          <div class="chart-container">
            <div ref="pressureChartRef" class="single-chart"></div>
            <div ref="flowChartRef" class="single-chart"></div>
            <div ref="temperatureChartRef" class="single-chart"></div>
          </div>
        </el-tab-pane>
        <el-tab-pane label="数据列表" name="table">
          <!-- 数据表格 -->
          <el-table :data="pagedHistoryData" style="width: 100%">
            <el-table-column prop="timestamp" label="时间" width="200">
              <template #default="scope">
                {{ formatDateTime(scope.row.timestamp) }}
              </template>
            </el-table-column>
            <el-table-column prop="pressure" label="压力 (MPa)" />
            <el-table-column prop="flow" label="流量 (m³/h)" />
            <el-table-column prop="temperature" label="温度 (°C)" />
            <el-table-column prop="status" label="状态">
              <template #default="scope">
                <el-tag :type="scope.row.status == 'normal' ? 'success' : 'warning'">
                  {{ scope.row.status == 'normal' ? '正常' : '预警' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="source_type" label="数据源" />
          </el-table>
          <div style="margin-top: 20px; display: flex; justify-content: flex-end;">
            <el-pagination
              v-model:current-page="pagination.currentPage"
              v-model:page-size="pagination.pageSize"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              :total="total"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script>
import * as echarts from 'echarts'

export default {
  name: 'History',
  data() {
    return {
      devices: [],
      timeRange: '1h',
      activeTab: 'chart',
      filterForm: {
        device_id: '',
        start_time: new Date(Date.now() - 3600000),
        end_time: new Date()
      },
      historyData: [],
      pagination: {
        currentPage: 1,
        pageSize: 20
      },
      total: 0,
      pressureChart: null,
      flowChart: null,
      temperatureChart: null
    }
  },
  computed: {
    routeDeviceId() {
      return this.$route.params.device_id
    },
    pagedHistoryData() {
      const start = (this.pagination.currentPage - 1) * this.pagination.pageSize
      const end = start + this.pagination.pageSize
      return this.historyData.slice(start, end)
    }
  },
  mounted() {
    this.loadDevices()
    this.initChart()
  },
  watch: {
    routeDeviceId: {
      handler(newVal) {
        if (newVal) {
          this.filterForm.device_id = newVal
          this.loadHistoryData()
        }
      },
      immediate: true
    }
  },
  beforeUnmount() {
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
        const response = await this.$axios.get('/device/list', {
          params: { page: 1, page_size: 100 }
        })
        this.devices = Array.isArray(response.data.devices) ? response.data.devices : []
        if (this.routeDeviceId) {
          this.filterForm.device_id = this.routeDeviceId
        } else if (!this.filterForm.device_id && this.devices.length > 0) {
          this.filterForm.device_id = this.devices[0].device_id
        }
        this.loadHistoryData()
      } catch (error) {
        console.error('获取设备列表失败:', error)
        this.devices = []
      }
    },
    async loadHistoryData() {
      if (!this.filterForm.device_id) return

      if (!this.filterForm.start_time) {
        this.filterForm.start_time = new Date(Date.now() - 3600000)
      }
      if (!this.filterForm.end_time) {
        this.filterForm.end_time = new Date()
      }

      try {
        const response = await this.$axios.get('/data/history/' + this.filterForm.device_id, {
          params: {
            start_time: this.formatLocalISO(this.filterForm.start_time),
            end_time: this.formatLocalISO(this.filterForm.end_time)
          }
        })
        this.historyData = response.data
        this.total = this.historyData.length
        this.pagination.currentPage = 1
        this.updateChart()
      } catch (error) {
        console.error('获取历史数据失败:', error)
      }
    },
    initChart() {
      // 初始化压力图表
      this.pressureChart = echarts.init(this.$refs.pressureChartRef)
      this.pressureChart.setOption({
        title: {
          text: '压力趋势',
          left: 'center',
          top: 4,
          textStyle: { fontSize: 14 }
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'cross', label: { backgroundColor: '#6a7985' } },
          formatter: function(params) {
            if (!params.length) return ''
            var result = params[0].name + '<br/>'
            for (var i = 0; i < params.length; i++) {
              result += params[i].marker + ' ' + params[i].seriesName + ': ' + params[i].value + '<br/>'
            }
            return result
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: []
        },
        yAxis: {
          type: 'value',
          name: '压力 (MPa)',
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
            smooth: true,
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
          left: 'center',
          top: 4,
          textStyle: { fontSize: 14 }
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'cross', label: { backgroundColor: '#6a7985' } },
          formatter: function(params) {
            if (!params.length) return ''
            var result = params[0].name + '<br/>'
            for (var i = 0; i < params.length; i++) {
              result += params[i].marker + ' ' + params[i].seriesName + ': ' + params[i].value + '<br/>'
            }
            return result
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: []
        },
        yAxis: {
          type: 'value',
          name: '流量 (m³/h)',
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
            smooth: true,
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
          left: 'center',
          top: 4,
          textStyle: { fontSize: 14 }
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'cross', label: { backgroundColor: '#6a7985' } },
          formatter: function(params) {
            if (!params.length) return ''
            var result = params[0].name + '<br/>'
            for (var i = 0; i < params.length; i++) {
              result += params[i].marker + ' ' + params[i].seriesName + ': ' + params[i].value + '<br/>'
            }
            return result
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: []
        },
        yAxis: {
          type: 'value',
          name: '温度 (°C)',
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
            smooth: true,
            lineStyle: {
              color: '#fac858'
            },
            itemStyle: {
              color: '#fac858'
            }
          }
        ]
      })
      
      window.addEventListener('resize', function() {
        if (this.pressureChart) this.pressureChart.resize()
        if (this.flowChart) this.flowChart.resize()
        if (this.temperatureChart) this.temperatureChart.resize()
      }.bind(this))
    },
    updateChart() {
      var timestamps = []
      var pressureData = []
      var flowData = []
      var temperatureData = []

      for (var i = 0; i < this.historyData.length; i++) {
        // 直接截取本地时间字符串中的 HH:MM 部分
        var ts = this.historyData[i].timestamp || ''
        timestamps.push(ts.length >= 16 ? ts.slice(11, 16) : ts)
        pressureData.push(this.historyData[i].pressure)
        flowData.push(this.historyData[i].flow)
        temperatureData.push(this.historyData[i].temperature)
      }
      
      // 更新压力图表
      if (this.pressureChart) {
        this.pressureChart.setOption({
          xAxis: {
            data: timestamps
          },
          series: [
            {
              data: pressureData
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
              data: flowData
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
              data: temperatureData
            }
          ]
        })
      }
    },
    handleTimeRangeChange() {
      if (this.timeRange === '1h') {
        this.filterForm.start_time = new Date(Date.now() - 3600000)
        this.filterForm.end_time = new Date()
      } else if (this.timeRange === '24h') {
        this.filterForm.start_time = new Date(Date.now() - 24 * 3600000)
        this.filterForm.end_time = new Date()
      } else if (this.timeRange === '72h') {
        this.filterForm.start_time = new Date(Date.now() - 72 * 3600000)
        this.filterForm.end_time = new Date()
      } else if (this.timeRange === 'custom') {
        // 为自定义时间范围设置默认值
        if (!this.filterForm.start_time) {
          this.filterForm.start_time = new Date(Date.now() - 3600000)
        }
        if (!this.filterForm.end_time) {
          this.filterForm.end_time = new Date()
        }
      }
      this.loadHistoryData()
    },
    handleSizeChange(val) {
      this.pagination.pageSize = val
      this.pagination.currentPage = 1
    },
    handleCurrentChange(val) {
      this.pagination.currentPage = val
    },
    exportData() {
      var dataStr = JSON.stringify(this.historyData, null, 2)
      var dataBlob = new Blob([dataStr], { type: 'application/json' })
      var url = URL.createObjectURL(dataBlob)
      var link = document.createElement('a')
      link.href = url
      link.download = 'device_' + this.filterForm.device_id + '_history_' + new Date().toISOString().split('T')[0] + '.json'
      link.click()
      URL.revokeObjectURL(url)
    },
    handleDeviceChange(deviceId) {
      this.filterForm.device_id = deviceId
      this.loadHistoryData()
    },
    clearDeviceFilter() {
      this.$router.push('/history')
    },
    formatLocalISO(date) {
      if (!date) return ''
      const d = date instanceof Date ? date : new Date(date)
      const pad = n => String(n).padStart(2, '0')
      return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
    },
    formatDateTime(timestamp) {
      if (!timestamp) return ''
      // 后端返回本地时间字符串，直接截取显示，避免时区转换问题
      if (typeof timestamp === 'string' && timestamp.length >= 16) {
        return timestamp.slice(0, 16).replace('T', ' ')
      }
      const date = new Date(timestamp)
      const pad = n => String(n).padStart(2, '0')
      return `${pad(date.getMonth()+1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
    }
  }
}
</script>

<style scoped>
.history {
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

.filter-card {
  margin-bottom: 20px;
}

.filter-form {
  margin-bottom: 0;
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

@media screen and (max-width: 1366px) {
  .page-title {
    font-size: 16px;
  }
  
  .single-chart {
    height: 250px;
  }
}

@media screen and (max-width: 1280px) {
  .page-title {
    font-size: 14px;
  }
  
  .single-chart {
    height: 230px;
  }
}

@media screen and (max-width: 768px) {
  .page-title {
    font-size: 14px;
  }
  
  .single-chart {
    height: 200px;
  }
  
  :deep(.el-pagination) {
    font-size: 12px;
  }
}
</style>
