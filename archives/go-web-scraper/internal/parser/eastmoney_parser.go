package parser

import (
	"bytes"
	"regexp"
	"strconv"
	"strings"
	"time"

	"go-web-scraper/internal/model"

	"github.com/PuerkitoBio/goquery"
)

type EastMoneyParser struct{}

func NewEastMoneyParser() *EastMoneyParser {
	return &EastMoneyParser{}
}

func (p *EastMoneyParser) Parse(html []byte) ([]model.EastMoneyNews, error) {
	doc, err := goquery.NewDocumentFromReader(bytes.NewReader(html))
	if err != nil {
		return nil, err
	}

	var newsList []model.EastMoneyNews
	today := time.Now().Format("2006-01-02")

	doc.Find(".news-item, .list-item, .item, li, div").Each(func(i int, s *goquery.Selection) {
		news := p.parseNewsItem(s, today)
		if news != nil {
			newsList = append(newsList, *news)
		}
	})

	if len(newsList) == 0 {
		newsList = p.parseTextFormat(doc, today)
	}

	return newsList, nil
}

func (p *EastMoneyParser) parseNewsItem(s *goquery.Selection, today string) *model.EastMoneyNews {
	timeText := strings.TrimSpace(s.Find(".time, .news-time").Text())
	titleText := strings.TrimSpace(s.Find(".title, .news-title").Text())
	contentText := strings.TrimSpace(s.Find(".content, .news-content").Text())
	href, _ := s.Find("a").Attr("href")

	if titleText == "" && contentText == "" {
		return nil
	}

	title, content := p.extractTitleAndContent(titleText, contentText)

	news := &model.EastMoneyNews{
		ID:          generateID(today, timeText, title),
		Title:       title,
		Content:     content,
		URL:         href,
		PublishTime: p.formatPublishTime(timeText, today),
		Source:      "东方财富快讯",
		CreatedAt:   time.Now(),
	}

	news.Stocks = p.parseStocks(s)

	return news
}

func (p *EastMoneyParser) parseTextFormat(doc *goquery.Document, today string) []model.EastMoneyNews {
	var newsList []model.EastMoneyNews

	bodyText := doc.Find("body").Text()
	lines := strings.Split(bodyText, "\n")

	var currentNews *model.EastMoneyNews
	timeRegex := regexp.MustCompile(`^\s*(\d{1,2}:\d{2})\s*$`)

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}

		if matches := timeRegex.FindStringSubmatch(line); len(matches) > 1 {
			if currentNews != nil && currentNews.Title != "" {
				currentNews.ID = generateID(today, currentNews.PublishTime, currentNews.Title)
				newsList = append(newsList, *currentNews)
			}
			currentNews = &model.EastMoneyNews{
				PublishTime: p.formatPublishTime(matches[1], today),
				Source:      "东方财富快讯",
				CreatedAt:   time.Now(),
			}
		} else if currentNews != nil {
			if currentNews.Title == "" {
				title, content := p.extractTitleAndContent(line, "")
				currentNews.Title = title
				if content != "" {
					currentNews.Content = content
				}
			} else if !strings.Contains(line, "点击查看全文") && currentNews.Content == "" {
				currentNews.Content = strings.ReplaceAll(line, "[点击查看全文]", "")
			}
		}
	}

	if currentNews != nil && currentNews.Title != "" {
		currentNews.ID = generateID(today, currentNews.PublishTime, currentNews.Title)
		newsList = append(newsList, *currentNews)
	}

	return newsList
}

func (p *EastMoneyParser) extractTitleAndContent(titleText, contentText string) (string, string) {
	title := titleText
	content := contentText

	if strings.Contains(title, "【") && strings.Contains(title, "】") {
		start := strings.Index(title, "【")
		end := strings.Index(title, "】")
		if end > start {
			title = strings.TrimSpace(title[start+3 : end])
			afterTitle := titleText[end+3:]
			if content == "" {
				content = strings.TrimSpace(afterTitle)
			}
		}
	}

	content = strings.ReplaceAll(content, "[点击查看全文]", "")
	content = strings.TrimSpace(content)

	return title, content
}

func (p *EastMoneyParser) parseStocks(s *goquery.Selection) []model.Stock {
	var stocks []model.Stock

	s.Find(".stock, .related-stock").Each(func(i int, stockSel *goquery.Selection) {
		name := strings.TrimSpace(stockSel.Find(".name, .stock-name").Text())
		changeText := strings.TrimSpace(stockSel.Find(".change, .stock-change").Text())

		if name == "" {
			name = strings.TrimSpace(stockSel.Text())
		}

		if name != "" {
			stock := model.Stock{
				Name:   name,
				Change: parseChange(changeText),
			}
			stocks = append(stocks, stock)
		}
	})

	return stocks
}

func (p *EastMoneyParser) formatPublishTime(timeText, today string) string {
	if timeText == "" {
		return today + " " + time.Now().Format("15:04")
	}

	timeText = strings.TrimSpace(timeText)
	if len(timeText) == 5 && strings.Contains(timeText, ":") {
		return today + " " + timeText
	}

	return timeText
}

func parseChange(text string) float64 {
	text = strings.TrimSpace(text)
	text = strings.TrimSuffix(text, "%")
	text = strings.TrimPrefix(text, "+")
	text = strings.TrimPrefix(text, "-")

	val, err := strconv.ParseFloat(text, 64)
	if err != nil {
		return 0
	}
	return val
}

func generateID(date, timeStr, title string) string {
	if len(title) > 20 {
		title = title[:20]
	}
	title = regexp.MustCompile(`[^\w\u4e00-\u9fa5]`).ReplaceAllString(title, "")
	return date + "_" + timeStr + "_" + title
}
