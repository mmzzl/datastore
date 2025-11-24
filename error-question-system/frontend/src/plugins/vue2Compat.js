// Vue 2 兼容性插件，用于支持uview-ui等依赖Vue 2 API的库
export default {
  install(app) {
    // 创建Vue.filter方法的全局兼容性
    if (typeof window !== 'undefined') {
      window.Vue = {
        filter: function(name, filter) {
          if (!window.Vue.filters) {
            window.Vue.filters = {};
          }
          window.Vue.filters[name] = filter;
          // 同时添加到全局属性中
          app.config.globalProperties.$filters[name] = filter;
        },
        filters: {},
        // 添加其他可能需要的Vue 2 API
        directive: function(name, directive) {
          app.directive(name, directive);
        },
        component: function(name, component) {
          app.component(name, component);
        },
        use: function(plugin, options) {
          app.use(plugin, options);
        },
        mixin: function(mixin) {
          app.mixin(mixin);
        },
        config: app.config,
        // 创建一个兼容的prototype对象
        prototype: app.config.globalProperties
      };
    }
    
    // 添加$filter到全局属性
    app.config.globalProperties.$filters = {};
    
    // 添加filter方法到app实例
    app.filter = function(name, filter) {
      if (!app.config.globalProperties.$filters) {
        app.config.globalProperties.$filters = {};
      }
      app.config.globalProperties.$filters[name] = filter;
      if (typeof window !== 'undefined' && window.Vue) {
        window.Vue.filters[name] = filter;
      }
      return app;
    };
    
    // 确保Vue.prototype指向globalProperties
    if (typeof window !== 'undefined' && window.Vue) {
      Object.defineProperty(window.Vue, 'prototype', {
        get: function() {
          return app.config.globalProperties;
        },
        set: function(value) {
          // 将属性复制到globalProperties
          Object.assign(app.config.globalProperties, value);
        }
      });
    }
  }
}