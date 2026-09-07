#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

/* Blender 4.5's headless OpenGL context ignores CUDA_VISIBLE_DEVICES.
 * Resolve its EGL default display to the explicitly assigned EGL device.
 * This shim is scoped to this render process, never the system loader. */
typedef void *(*Lookup)(void *, const char *);
static void *native_symbol(const char *name) {
    Lookup lookup=(Lookup)dlvsym(RTLD_NEXT,"dlsym","GLIBC_2.2.5");
    void *egl=dlopen("libEGL.so.1",RTLD_LAZY|RTLD_LOCAL);
    return lookup(egl,name);
}
static void *assigned_display(void *native) {
    const char *selected=getenv("PARIS_EGL_GPU");
    if (!selected) return ((void *(*)(void *))native_symbol("eglGetDisplay"))(native);
    void *(*getproc)(const char *)=native_symbol("eglGetProcAddress");
    unsigned (*query)(int,void **,int *)=getproc("eglQueryDevicesEXT");
    unsigned (*attrib)(void *,int,intptr_t *)=getproc("eglQueryDeviceAttribEXT");
    void *(*display)(unsigned,void *,const int *)=getproc("eglGetPlatformDisplayEXT");
    if (!query||!attrib||!display) {fprintf(stderr,"EGL device API unavailable\n"); exit(90);}
    void *devices[32];int count=0;int wanted=atoi(selected);
    if (!query(32,devices,&count)) exit(91);
    for (int i=0;i<count;i++) {
        intptr_t cuda=-1;
        unsigned valid=attrib(devices[i],0x323A,&cuda);
        if (valid && cuda==wanted) {
            fprintf(stderr,"PARIS_EGL_BOUND cuda=%ld egl=%d\n",(long)cuda,i);
            return display(0x313F,devices[i],NULL);
        }
    }
    fprintf(stderr,"Assigned CUDA device %d not found among %d EGL devices\n",wanted,count);
    exit(92);
}
void *dlsym(void *handle,const char *name) {
    Lookup lookup=(Lookup)dlvsym(RTLD_NEXT,"dlsym","GLIBC_2.2.5");
    void *resolved=lookup(handle,name);
    if (strcmp(name,"eglGetDisplay")==0 && resolved==native_symbol(name)) return (void *)assigned_display;
    return resolved;
}
