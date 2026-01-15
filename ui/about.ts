import { mount } from 'svelte'
import './style.css'
import App from './about.svelte'

const app = mount(App, {
  target: document.getElementById('app')!,
})

export default app
