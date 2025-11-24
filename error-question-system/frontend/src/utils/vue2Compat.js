// Vue 2 兼容性文件
// 确保在导入uview-ui之前，Vue对象已经完全设置好

// 创建Vue 2兼容性对象
const Vue2Compat = {
  // 确保Vue.prototype存在并且可以设置属性
  prototype: {},
  
  // 确保Vue.filters存在
  filters: {},
  
  // 添加Vue.filter方法
  filter: function(name, filter) {
    this.filters[name] = filter;
    // 同时添加到app.config.globalProperties
    if (this._app && this._app.config && this._app.config.globalProperties) {
      this._app.config.globalProperties[name] = filter;
    }
  },
  
  // 其他Vue 2方法
  directive: function(name, directive) {
    if (this._app) {
      this._app.directive(name, directive);
    }
  },
  component: function(name, component) {
    if (this._app) {
      this._app.component(name, component);
    }
  },
  use: function(plugin, options) {
    if (this._app) {
      this._app.use(plugin, options);
    }
  },
  mixin: function(mixin) {
    if (this._app) {
      this._app.mixin(mixin);
    }
  },
  
  // 初始化方法，设置app实例
  init: function(app) {
    this._app = app;
    this.config = app.config;
    
    // 确保Vue.prototype.$u存在，这是uview-ui需要的
    if (!this.prototype.$u) {
      this.prototype.$u = {};
    }
    
    // 监听Vue.prototype的变化，将属性同步到app.config.globalProperties
    const tempPrototype = this.prototype;
    Object.defineProperty(this, 'prototype', {
      get: function() {
        return tempPrototype;
      },
      set: function(value) {
        // 当设置Vue.prototype时，将属性复制到tempPrototype和globalProperties
        Object.assign(tempPrototype, value);
        if (this._app && this._app.config && this._app.config.globalProperties) {
          Object.assign(this._app.config.globalProperties, value);
        }
      }
    });
  }
};

// 导出兼容性对象
export default Vue2Compat;