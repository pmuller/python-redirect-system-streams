/*
 * Build (on my mac):
 *
 *  gcc -fno-common -fPIC -dynamiclib -o libhello.dylib hello.c
 *
 * On Linux, this should work:
 *
 *  gcc -fno-common -fPIC -shared -o libhello.so hello.c
 *
 */

#include <stdio.h>


void hello(char *name)
{
    printf("hello %s\n", name);
}


void many_hello(char *name, int count)
{
    char buf[64];

    for (int i = 0; i < count; i++)
    {
        snprintf(buf, 64, "%s (%d)", name, i);
        hello(buf);
    }
}


void err_hello(char *name)
{
    fprintf(stderr, "hello %s\n", name);
}


int add(int a, int b)
{
    return a + b;
}
