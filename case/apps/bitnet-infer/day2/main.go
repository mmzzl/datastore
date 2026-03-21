package main 
import "fmt"


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
}