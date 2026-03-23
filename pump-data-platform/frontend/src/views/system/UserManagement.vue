<template>
  <div class="user-management">
    <h2>用户管理</h2>
    <el-card>
      <div class="card-header">
        <el-button type="primary" @click="handleAddUser">
          <el-icon><i-ep-plus /></el-icon> 新增用户
        </el-button>
      </div>
      <el-table :data="pagedUsers" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="role" label="角色" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button type="primary" size="small" @click="handleEditUser(scope.row)">
              编辑
            </el-button>
            <el-button type="danger" size="small" @click="handleDeleteUser(scope.row.id)">
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
          :total="users.length"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 新增/编辑用户对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!form.id">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" placeholder="请选择角色">
            <el-option label="超级管理员" value="superadmin" />
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
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
  name: 'UserManagement',
  data() {
    return {
      users: [
        { id: 1, username: 'admin', role: 'superadmin', created_at: new Date().toISOString() },
        { id: 2, username: 'test', role: 'user', created_at: new Date().toISOString() }
      ],
      pagination: {
        currentPage: 1,
        pageSize: 20
      },
      dialogVisible: false,
      dialogTitle: '新增用户',
      form: {
        id: null,
        username: '',
        password: '',
        role: ''
      },
      rules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' }
        ],
        role: [
          { required: true, message: '请选择角色', trigger: 'blur' }
        ]
      }
    }
  },
  computed: {
    pagedUsers() {
      const start = (this.pagination.currentPage - 1) * this.pagination.pageSize
      const end = start + this.pagination.pageSize
      return this.users.slice(start, end)
    }
  },
  methods: {
    handleAddUser() {
      this.dialogTitle = '新增用户'
      this.form = { id: null, username: '', password: '', role: '' }
      this.dialogVisible = true
    },
    handleEditUser(user) {
      this.dialogTitle = '编辑用户'
      this.form = { ...user }
      this.dialogVisible = true
    },
    async handleSubmit() {
      const valid = await this.$refs.formRef.validate()
      if (!valid) return
      
      if (this.form.id) {
        // 编辑用户
        const index = this.users.findIndex(u => u.id === this.form.id)
        if (index !== -1) {
          this.users[index] = { ...this.form }
          this.$message.success('编辑成功')
        }
      } else {
        // 新增用户
        const newUser = {
          id: this.users.length + 1,
          ...this.form,
          created_at: new Date().toISOString()
        }
        this.users.push(newUser)
        this.$message.success('新增成功')
      }
      
      this.dialogVisible = false
    },
    handleDeleteUser(id) {
      this.$confirm('确定要删除此用户吗？', '警告', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.users = this.users.filter(u => u.id !== id)
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
.user-management {
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