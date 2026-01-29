#include <stdio.h>

int main() {
    int n, i;
    float cpu[100];

    printf("Enter number of CPU readings: ");
    scanf("%d", &n);

    for(i = 0; i < n; i++) {
        printf("Enter CPU usage %d: ", i + 1);
        scanf("%f", &cpu[i]);
    }

    printf("\nSystem Health Analysis:\n");
    for(i = 0; i < n; i++) {
        if(cpu[i] > 80)
            printf("Reading %.2f%% -> CRITICAL\n", cpu[i]);
        else
            printf("Reading %.2f%% -> NORMAL\n", cpu[i]);
    }

    return 0;
}