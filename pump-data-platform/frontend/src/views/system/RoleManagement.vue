<template>
  <div class="role-management">
    <h2>角色管理</h2>
    <el-card>
      <div class="card-header">
        <el-button type="primary" @click="handleAddRole">
          <el-icon><i-ep-plus /></el-icon> 新增角色
        </el-button>
      </div>
      <el-table :data="pagedRoles" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="角色名称" />
        <el-table-column prop="description" label="角色描述" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button type="primary" size="small" @click="handleEditRole(scope.row)">
              编辑
            </el-button>
            <el-button type="danger" size="small" @click="handleDeleteRole(scope.row.id)">
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
          :total="roles.length"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 新增/编辑角色对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="角色名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入角色名称" />
        </el-form-item>
        <el-form-item label="角色描述" prop="description">
          <el-input v-model="form.description" type="textarea" placeholder="请输入角色描述" />
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
  name: 'RoleManagement',
  data() {
    return {
      roles: [
        { id: 1, name: '超级管理员', description: '拥有系统所有权限', created_at: new Date().toISOString() },
        { id: 2, name: '管理员', description: '拥有管理权限', created_at: new Date().toISOString() },
        { id: 3, name: '普通用户', description: '拥有查看权限', created_at: new Date().toISOString() }
      ],
      pagination: {
        currentPage: 1,
        pageSize: 20
      },
      dialogVisible: false,
      dialogTitle: '新增角色',
      form: {
        id: null,
        name: '',
        description: ''
      },
      rules: {
        name: [
          { required: true, message: '请输入角色名称', trigger: 'blur' }
        ],
        description: [
          { required: true, message: '请输入角色描述', trigger: 'blur' }
        ]
      }
    }
  },
  computed: {
    pagedRoles() {
      const start = (this.pagination.currentPage - 1) * this.pagination.pageSize
      const end = start + this.pagination.pageSize
      return this.roles.slice(start, end)
    }
  },
  methods: {
    handleAddRole() {
      this.dialogTitle = '新增角色'
      this.form = { id: null, name: '', description: '' }
      this.dialogVisible = true
    },
    handleEditRole(role) {
      this.dialogTitle = '编辑角色'
      this.form = { ...role }
      this.dialogVisible = true
    },
    async handleSubmit() {
      const valid = await this.$refs.formRef.validate()
      if (!valid) return
      
      if (this.form.id) {
        // 编辑角色
        const index = this.roles.findIndex(r => r.id === this.form.id)
        if (index !== -1) {
          this.roles[index] = { ...this.form }
          this.$message.success('编辑成功')
        }
      } else {
        // 新增角色
        const newRole = {
          id: this.roles.length + 1,
          ...this.form,
          created_at: new Date().toISOString()
        }
        this.roles.push(newRole)
        this.$message.success('新增成功')
      }
      
      this.dialogVisible = false
    },
    handleDeleteRole(id) {
      this.$confirm('确定要删除此角色吗？', '警告', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.roles = this.roles.filter(r => r.id !== id)
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
.role-management {
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