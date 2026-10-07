import { defineConfig } from 'vite'
import base from '../../consultation10/browser/vite.config'
export default defineConfig({ ...base, server:{host:'127.0.0.1',port:60262,strictPort:true} })
