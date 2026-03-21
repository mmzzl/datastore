package main 
import (
	"fmt"
	"strings"
)

func isEven(num int) bool {
	return num%2 == 0
}

func squareAndCube(num int) (int, int) {
	return num*num, num*num*num
}

func max(nums ...int) int {
	if len(nums) == 0 {
		return 0
	}
	max := nums[0]
	for _, num := range nums {
		if num > max {
			max = num
		}
	}
	return max
}

func minMax(nums []int) (min, max int) {
	if len(nums) == 0 {
		return 0, 0
	}
	min = nums[0]
	max = nums[0]
	for _, num := range nums {
		if num < min {
			min = num
		}
		if num > max {
			max = num
		}
	}
	return min, max
}

func reverse(nums []int) []int {
	reversed := make([]int, 0, len(nums))
	for i := len(nums) - 1; i >= 0; i-- {
		reversed = append(reversed, nums[i])
	}
	return reversed
}

func unique(nums []int) []int {
	seen := make(map[int]bool)
	unique := make([]int, 0, len(nums))
	for _, num := range nums {
		if _, ok := seen[num]; !ok {
			unique = append(unique, num)
			seen[num] = true
		}
	}
	return unique
}

func mergeUnique(s1, s2 []int) []int {
	merged := append(s1, s2...)
	merged = unique(merged)
	return merged
}

func wordCount(text string) map[string]int {
	count := make(map[string]int)
	words := strings.Split(text, " ")
	for _, word := range words {
		count[word]++
	}
	return count
}

func intersect(m1, m2 map[string]int) map[string]int {
	intersect := make(map[string]int)
	for word, count := range m1 {
		if _, ok := m2[word]; ok {
			intersect[word] = count
		}
	}
	return intersect
}

func reverseMap(m map[string]int) map[int]string {
	reversed := make(map[int]string)
	for word, count := range m {
		reversed[count] = word
	}
	return reversed
}

func main() {
	// 猜数字
	// var target = 42
	// guess := 0
	// for {
	// 	fmt.Printf("请输入一个整数:")
	// 	fmt.Scan(&guess)
	// 	if guess == target {
	// 		fmt.Println("恭喜你猜对了！")
	// 		break
	// 	} else if guess < target {
	// 		fmt.Println("你猜的数字太小了！")
	// 	} else {
	// 		fmt.Println("你猜的数字太大了！")
	// 	}
	// }
	// 打印乘法表
	for i :=1; i<=9; i++ {
		for j :=1; j<=i; j++ {
			fmt.Printf("%d*%d=%d\t", i, j, i*j)
		}
		fmt.Println()
	}
	// 成绩等级判断
	score := 80
	if score >= 90 {
		fmt.Println("A")
	} else if score >= 80 {
		fmt.Println("B")
	} else if score >= 70 {
		fmt.Println("C")
	} else if score >= 60 {
		fmt.Println("D")
	} else {
		fmt.Println("E")
	}
	// switch 版本
	switch {
	case score >= 90:
		fmt.Println("A")
	case score >= 80:
		fmt.Println("B")
	case score >= 70:
		fmt.Println("C")
	case score >= 60:
		fmt.Println("D")
	default:
		fmt.Println("E")
	}
	// 奇偶统计
	evenCount := 0
	oddCount := 0
	for i := 1; i<=100; i++ {
		if i%2 == 0 {
			evenCount++
		} else {
			oddCount++
		}
	}
	fmt.Printf("1-100 中有 %d 个偶数，%d 个奇数\n", evenCount, oddCount)
	// 数字分解
	num := 123
	digits := make([]int, 0, 3)
	for num > 0 {
		digit := num % 10
		digits = append(digits, digit)
		num /= 10
	}
	for i := len(digits) - 1; i >= 0; i-- {
    	fmt.Printf("%d ", digits[i])
	}
	fmt.Println()
	// 猜拳游戏
	// 判断奇偶
	if isEven(4) {
		fmt.Println("4 是偶数")
	} else {
		fmt.Println("4 不是偶数")
	}
	// 计算平方和立方
	square, cube := squareAndCube(3)
	fmt.Printf("3 的平方是 %d，立方是 %d\n", square, cube)
	// 找最大值
	maxNum := max(1, 2, 3, 4, 5)
	fmt.Printf("最大值是 %d\n", maxNum)
	// 创建一个空切片
	slice := make([]int, 0)
	fmt.Printf("空切片: %v\n", slice)
	// 添加5个元素
	// slice = []int{}
	slice = make([]int, 0, 5)
	slice = append(slice, 1, 2, 3, 4, 5)
	fmt.Printf("添加5个元素后的切片: %v\n", slice)
	// 打印长度和容量
	fmt.Printf("切片长度: %d,容量: %d\n", len(slice), cap(slice))
	// 删除第3个元素
	slice = append(slice[:2], slice[3:]...)
	fmt.Printf("删除第3个元素后的切片: %v\n", slice)
	// 打印长度和容量
	fmt.Printf("删除第3个元素后的切片长度: %d,容量: %d\n", len(slice), cap(slice))
	// 找最小值和最大值
	min, max := minMax(slice)
	fmt.Printf("最小值是 %d,最大值是 %d\n", min, max)
	// 反转切片
	reversed := reverse(slice)
	fmt.Printf("反转后的切片: %v\n", reversed)
	// 合并切片
	merged := mergeUnique(slice, reversed)
	fmt.Printf("合并后的切片: %v\n", merged)
	// 统计单词出现次数
	text := "hello hello world go go go"
	count := wordCount(text)
	fmt.Printf("单词出现次数: %v\n", count)
	// 找交集
	count2 := map[string]int{"zhangsan":1, "lishi": 2, "go": 4}
	intersect := intersect(count, count2)
	fmt.Printf("交集: %v\n", intersect)
	// 反转映射
	reversed := reverseMap(count)
	fmt.Printf("反转后的映射: %v\n", reversed)
}