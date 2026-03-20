package main 

import "fmt" 

func add_two(a int, b int) int {
	return a + b
}

func main() {
	// 方式1：var + 变量名 + 类型
	var name string = "雪松"
	var job := "工程师"  // Go 会自动推断 job 是 string 类型
	var age int = 25
	score := 90 
	var isGopher bool = true
	hobby := "写代码"
	fmt.Printf("姓名：%s\n", name)
	fmt.Printf("年龄：%d\n", age)
	fmt.Printf("职业：%s\n", job)
	fmt.Printf("爱好：%s\n", hobby)

	result := add_two(1, 2)
	fmt.Printf("result: %d\n", result)
	fmt.Printf("isGopher: %v\n", isGopher)
}
