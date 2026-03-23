<template>
  <div class="menu-management">
    <h2>菜单管理</h2>
    <el-card>
      <div class="card-header">
        <el-button type="primary" @click="handleAddMenu">
          <el-icon><i-ep-plus /></el-icon> 新增菜单
        </el-button>
      </div>
      <el-table :data="pagedMenus" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="菜单名称" />
        <el-table-column prop="path" label="路由路径" />
        <el-table-column prop="icon" label="图标" />
        <el-table-column prop="parent_id" label="父菜单ID" width="120" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button type="primary" size="small" @click="handleEditMenu(scope.row)">
              编辑
            </el-button>
            <el-button type="danger" size="small" @click="handleDeleteMenu(scope.row.id)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="menus.length"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 新增/编辑菜单对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="菜单名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入菜单名称" />
        </el-form-item>
        <el-form-item label="路由路径" prop="path">
          <el-input v-model="form.path" placeholder="请输入路由路径" />
        </el-form-item>
        <el-form-item label="图标" prop="icon">
          <el-input v-model="form.icon" placeholder="请输入图标名称" />
        </el-form-item>
        <el-form-item label="父菜单ID" prop="parent_id">
          <el-input v-model="form.parent_id" type="number" placeholder="请输入父菜单ID" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
export default {
  name: 'MenuManagement',
  data() {
    return {
      menus: [
        { id: 1, name: '实时监控', path: '/', icon: 'monitor', parent_id: 0, created_at: new Date().toISOString() },
        { id: 2, name: '设备列表', path: '/device-list', icon: 'list', parent_id: 0, created_at: new Date().toISOString() },
        { id: 3, name: '历史数据', path: '/history', icon: 'data-line', parent_id: 0, created_at: new Date().toISOString() },
        { id: 4, name: '预警管理', path: '/warning', icon: 'warning', parent_id: 0, created_at: new Date().toISOString() },
        { id: 5, name: '配置中心', path: '/config', icon: 'setting', parent_id: 0, created_at: new Date().toISOString() },
        { id: 6, name: '数据源配置', path: '/data-source-config', icon: '', parent_id: 5, created_at: new Date().toISOString() },
        { id: 7, name: '设备阈值配置', path: '/device-threshold-config', icon: '', parent_id: 5, created_at: new Date().toISOString() },
        { id: 8, name: '边缘网关', path: '/gateway', icon: 'cpu', parent_id: 0, created_at: new Date().toISOString() },
        { id: 9, name: '系统设置', path: '/system', icon: 'tools', parent_id: 0, created_at: new Date().toISOString() },
        { id: 10, name: '用户管理', path: '/system/user', icon: '', parent_id: 9, created_at: new Date().toISOString() },
        { id: 11, name: '角色管理', path: '/system/role', icon: '', parent_id: 9, created_at: new Date().toISOString() },
        { id: 12, name: '菜单管理', path: '/system/menu', icon: '', parent_id: 9, created_at: new Date().toISOString() }
      ],
      pagination: {
        currentPage: 1,
        pageSize: 20
      },
      dialogVisible: false,
      dialogTitle: '新增菜单',
      form: {
        id: null,
        name: '',
        path: '',
        icon: '',
        parent_id: 0
      },
      rules: {
        name: [
          { required: true, message: '请输入菜单名称', trigger: 'blur' }
        ],
        path: [
          { required: true, message: '请输入路由路径', trigger: 'blur' }
        ]
      }
    }
  },
  computed: {
    pagedMenus() {
      const start = (this.pagination.currentPage - 1) * this.pagination.pageSize
      const end = start + this.pagination.pageSize
      return this.menus.slice(start, end)
    }
  },
  methods: {
    handleAddMenu() {
      this.dialogTitle = '新增菜单'
      this.form = { id: null, name: '', path: '', icon: '', parent_id: 0 }
      this.dialogVisible = true
    },
    handleEditMenu(menu) {
      this.dialogTitle = '编辑菜单'
      this.form = { ...menu }
      this.dialogVisible = true
    },
    async handleSubmit() {
      const valid = await this.$refs.formRef.validate()
      if (!valid) return
      
      if (this.form.id) {
        // 编辑菜单
        const index = this.menus.findIndex(m => m.id === this.form.id)
        if (index !== -1) {
          this.menus[index] = { ...this.form }
          this.$message.success('编辑成功')
        }
      } else {
        // 新增菜单
        const newMenu = {
          id: this.menus.length + 1,
          ...this.form,
          created_at: new Date().toISOString()
        }
        this.menus.push(newMenu)
        this.$message.success('新增成功')
      }
      
      this.dialogVisible = false
    },
    handleDeleteMenu(id) {
      this.$confirm('确定要删除此菜单吗？', '警告', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.menus = this.menus.filter(m => m.id !== id)
        this.$message.success('删除成功')
      }).catch(() => {})
    },
    handleSizeChange(size) {
      this.pagination.pageSize = size
      this.pagination.currentPage = 1
    },
    handleCurrentChange(current) {
      this.pagination.currentPage = current
    },
    formatDateTime(timestamp) {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')
      const seconds = String(date.getSeconds()).padStart(2, '0')
      return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
    }
  }
}
</script>

<style scoped>
.menu-management {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>