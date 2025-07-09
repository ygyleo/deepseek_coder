
// 添加必要的函数声明
void* malloc(size_t size);
void free(void* ptr);
void* realloc(void* ptr, size_t size);
size_t strlen(const char* str);
char* strcpy(char* dest, const char* src);
char* strcat(char* dest, const char* src);
int strcmp(const char* str1, const char* str2);
char* strchr(const char* str, int c);
void* memcpy(void* dest, const void* src, size_t n);
int printf(const char* format, ...);
int scanf(const char* format, ...);
int isspace(int c);
int isalpha(int c);

int *func0(int *numbers, int size) {
    if (size <= 0) {
        return NULL;
    }
    
    int *out = malloc(size * sizeof(int));
    if (!out) {
        return NULL;
    }
    
    int max = numbers[0];
    for (int i = 0; i < size; i++) {
        if (numbers[i] > max) max = numbers[i];
        out[i] = max;
    }
    return out;
}