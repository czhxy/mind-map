# hardfault调试案例

```
PC=0x0800088A(死循环)  →  只是 HardFault_Handler，不是崩溃点
LR=0xFFFFFFFD          →  Thread模式+PSP，FreeRTOS任务里崩的
PSP=0x20000698         →  栈帧在这里
栈帧[PSP+0x18]=0x0800141A  →  真正故障点 _printf_core
CFSR=0x00000400        →  IMPRECISERR 不精确总线错误（写越界）
HFSR=0x40000000        →  FORCED，由BusFault升级
反查代码              →  char *buf 野指针 + sprintf
```