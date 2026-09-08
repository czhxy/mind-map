# LeetCode

## 1.翻转链表

思路：

![image-20260906201314700](C:\Users\cz\AppData\Roaming\Typora\typora-user-images\image-20260906201314700.png)                



``` c
struct ListNode* reverseList(struct ListNode* head) {

  struct ListNode* curr = head;

  struct ListNode* prev = NULL;

  while (curr != NULL) {

​    struct ListNode* nexttmep = curr->next;

​    curr->next = prev;

​    prev = curr;

​    curr = nexttmep;

  }
  

  return prev;

}
```



## 2.最长公共前缀

```c
char* longestCommonPrefix(char** strs, int strsSize) {
    char* first = strs[0];
    int max_len = strlen(first);
    char* result = (char*)malloc(1+(max_len * sizeof(char)));
    int i = 0;
    for (i = 0; i < max_len; i++) {
        char c = strs[0][i];
        for (int j = 0; j < strsSize; j++) {
            if (strs[j][i] == '\0' || strs[j][i] != c) {
                result[i] = '\0';
                return result;
            }
        }
        result[i] = c;
    }
    result[i] = '\0';
    return result;
}
```



## 3.字符串第一个匹配的下标

```c
int strStr(char* haystack, char* needle) {
    int len_h = strlen(haystack);
    int len_n = strlen(needle);

    for (int i = 0; i < len_h; i++) {
        if (haystack[i] == needle[0]) {
            for (int j = 0; j < len_n; j++) {
                if (haystack[i + j] != needle[j]) {
                    break;
                }
                if (j == len_n - 1) {
                    return i;
                }
            }
        }
    }
    return -1;
}
```



## 4.判断子序列

```c
bool isSubsequence(char* s, char* t) {
    int max_len_t = strlen(t);
    int max_len_s = strlen(s);
    int count = 0;
    for (int i = 0; i < max_len_t; i++) {
        if (t[i] == s[count]) {
            count++;
        }
    }
    if (count == max_len_s) {
        return true;
    } else {
        return false;
    }
}
```



## 5.二分查找

```c
int searchInsert(int* nums, int numsSize, int target) {
    int left = 0;
    int right = numsSize - 1;
    int mid = 0;
    while (left <= right) {
        mid = (left + right) / 2;
        if (nums[mid] >= target) {
            right = mid - 1;
        } else {
            left = mid + 1;
        }
    }
    return left;
}
```

注意左闭右闭区间



## 6.合并两个有序链表

```c
/**
 * Definition for singly-linked list.
 * struct ListNode {
 *     int val;
 *     struct ListNode *next;
 * };
 */
struct ListNode* mergeTwoLists(struct ListNode* list1, struct ListNode* list2) {
    struct ListNode* dummynode=(struct ListNode *)malloc(sizeof(struct ListNode));
    dummynode->next = NULL;
    struct ListNode* curr = dummynode;
    while (list1 && list2) {
        if (list1->val < list2->val) {
            curr->next = list1;
            list1 = list1->next;
        } else {
            curr->next = list2;
            list2 = list2->next;
        }
        curr = curr->next;
    }
    if (list1) {
        curr->next = list1;
    }
    if (list2) {
        curr->next = list2;
    }
    return dummynode->next;
}
```

## 7.反转链表II

```c
/**
 * Definition for singly-linked list.
 * struct ListNode {
 *     int val;
 *     struct ListNode *next;
 * };
 */
struct ListNode* reverseList(struct ListNode* head) {
    struct ListNode* prev = NULL;
    struct ListNode* curr = head;
    while (curr != NULL) {
        struct ListNode* nexttemp = curr->next;
        curr->next = prev;
        prev = curr;
        curr = nexttemp;
    }
    return prev;
}
struct ListNode* reverseBetween(struct ListNode* head, int left, int right) {
    struct ListNode* dummynode =
        (struct ListNode*)malloc(sizeof(struct ListNode));
    dummynode->val = -1;
    dummynode->next = head;
    struct ListNode* pre = dummynode;
    for (int i = 0; i < left - 1; i++) {
        pre = pre->next;
    }
    struct ListNode* rightnode = pre;
    for (int i = 0; i < right - left + 1; i++) {
        rightnode = rightnode->next;
    }
    struct ListNode* leftnode = pre->next;
    struct ListNode* curr = rightnode->next;
    pre->next = NULL;
    rightnode->next = NULL;
    struct ListNode* reverse = reverseList(leftnode);
    pre->next = rightnode;
    leftnode->next = curr;
    return dummynode->next;
}
```

