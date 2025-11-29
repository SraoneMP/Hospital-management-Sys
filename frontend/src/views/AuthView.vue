<template>
  <div class="min-vh-100 d-flex align-items-center">
    <div class="container">
      <div class="row justify-content-center">
        <div class="col-12 col-md-7 col-lg-5">
          <div class="card shadow-sm">
            <div class="card-body p-4">
              <div class="text-center mb-3">
                <h2 class="mb-0 page-title">{{ showLogin ? 'Welcome back' : 'Create your account' }}</h2>
              </div>

              <ul class="nav nav-pills nav-fill mb-3" role="tablist">
                <li class="nav-item" role="presentation">
                  <button class="nav-link" :class="{active: showLogin}" @click="flipMode(true)" type="button">Login</button>
                </li>
                <li class="nav-item" role="presentation">
                  <button class="nav-link" :class="{active: !showLogin}" @click="flipMode(false)" type="button">Register</button>
                </li>
              </ul>

              <!-- Login -->
              <form v-if="showLogin" @submit.prevent="attemptLogin" class="row g-3">
                <div class="col-12">
                  <label for="email" class="form-label">Email</label>
                  <input id="email" v-model="email" type="email" class="form-control" placeholder="you@example.com" required />
                </div>
                <div class="col-12">
                  <label for="password" class="form-label">Password</label>
                  <input id="password" v-model="password" type="password" class="form-control" placeholder="••••••••" required />
                </div>

                <div v-if="notice" class="col-12">
                  <div :class="['alert', loginGood ? 'alert-success' : 'alert-danger']">{{ notice }}</div>
                </div>

                <div class="col-12 d-grid">
                  <button class="btn btn-primary" type="submit" :disabled="busy">
                    {{ busy ? 'Signing in...' : 'Sign in' }}
                  </button>
                </div>
                <div class="col-12 text-center">
                  <span class="small text-muted">Don't have an account?</span>
                  <button class="btn btn-link btn-sm" type="button" @click="flipMode(false)">Register</button>
                </div>
              </form>

              <!-- Register (Patient) -->
              <form v-else @submit.prevent="attemptRegister" class="row g-3">
                <div class="col-12">
                  <label for="name" class="form-label">Full Name</label>
                  <input id="name" v-model="fullName" type="text" class="form-control" placeholder="Your name" required />
                </div>
                <div class="col-12">
                  <label for="reg_email" class="form-label">Email</label>
                  <input id="reg_email" v-model="email" type="email" class="form-control" placeholder="you@example.com" required />
                </div>
                <div class="col-12">
                  <label for="reg_password" class="form-label">Password</label>
                  <input id="reg_password" v-model="password" type="password" class="form-control" placeholder="Minimum 6 characters" required />
                </div>

                <div v-if="notice" class="col-12">
                  <div :class="['alert', registerGood ? 'alert-success' : 'alert-danger']">{{ notice }}</div>
                </div>

                <div class="col-12 d-grid">
                  <button class="btn btn-primary" type="submit" :disabled="busy">
                    {{ busy ? 'Creating account...' : 'Create account' }}
                  </button>
                </div>
                <div class="col-12 text-center">
                  <span class="small text-muted">Already have an account?</span>
                  <button class="btn btn-link btn-sm" type="button" @click="flipMode(true)">Login</button>
                </div>
              </form>

            </div>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AuthView',
  data() {
    return {
      showLogin: true,
      fullName: '',
      notice: '',
      loginGood: false,
      registerGood: false,
      busy: false,
      email: '',
      password: '',
    };
  },
  methods: {
    flipMode(toLogin) {
      this.notice = '';
      this.loginGood = false;
      this.registerGood = false;
      this.showLogin = toLogin;
    },

    async attemptLogin() {
      this.busy = true;
      this.loginGood = false;
      this.notice = '';
      try {
        const resp = await fetch('/api/auth', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: this.email, password: this.password }),
        });

        const text = await resp.text();
        let data;
        try {
          data = JSON.parse(text);
        } catch {
          this.notice = 'Server error: Invalid response';
          return;
        }

        if (!resp.ok) {
          this.notice = data.message || 'Login failed';
          return;
        }

        this.loginGood = true;
        this.notice = 'Login successful';
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        localStorage.setItem('user_id', data.user.id);

        // route by role — nudge App.vue to refresh its state
        if (data.user?.role === 'admin') {
          this.$router.push('/admin').then(() => window.location.reload());
        } else if (data.user?.role === 'doctor') {
          this.$router.push('/doctor').then(() => window.location.reload());
        } else {
          this.$router.push('/patient').then(() => window.location.reload());
        }
      } catch (e) {
        console.error(e);
        this.notice = 'Login failed. Please check your credentials.';
      } finally {
        this.busy = false;
      }
    },

    async attemptRegister() {
      this.busy = true;
      this.registerGood = false;
      this.notice = '';
      try {
        const resp = await fetch('/api/auth', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: this.fullName, email: this.email, password: this.password }),
        });

        let data = null;
        try {
          data = await resp.json();
        } catch {
          this.notice = 'Server error: Invalid response';
          return;
        }

        if (!resp.ok) {
          this.notice = data?.message || 'Registration failed';
          return;
        }

        this.registerGood = true;
        this.notice = 'Registration successful! Please login.';
        setTimeout(() => this.flipMode(true), 800);
      } catch (e) {
        console.error(e);
        this.notice = 'Registration failed. Please try again.';
      } finally {
        this.busy = false;
      }
    },
  },
};
</script>

<style scoped>
.min-vh-100 { min-height: 100vh; }
.card { border-radius: var(--radius); }
.nav-pills .nav-link {
  border-radius: 999px;
}
.nav-pills .nav-link.active {
  background: var(--primary);
}
.page-title { font-weight: 700; }
</style>
