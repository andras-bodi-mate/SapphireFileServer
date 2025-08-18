import { createApp } from 'vue'
import App from './App.vue'
import shortkey from 'vue3-shortkey'

import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

const vuetify = createVuetify({
  components,
  directives,
})

createApp(App)
  .use(vuetify)
  .use(shortkey)
  .mount('#app')