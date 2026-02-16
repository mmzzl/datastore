package parser

import (
	"bytes"

	"github.com/PuerkitoBio/goquery"
)

type FilterFunc func([]string) []string

type ParseResult struct {
	Data []string
}

type ParseRule struct {
	Type    string
	Rule    string
	Attrs   string
	Filters []FilterFunc
}

type Parser interface {
	Parse(doc []byte, rule ParseRule) (*ParseResult, error)
}

type CSSParser struct{}

func NewCSSParser() *CSSParser {
	return &CSSParser{}
}

func (p *CSSParser) Parse(doc []byte, rule ParseRule) (*ParseResult, error) {
	document, err := goquery.NewDocumentFromReader(bytes.NewReader(doc))
	if err != nil {
		return nil, err
	}

	nodes := document.Find(rule.Rule)

	var results []string
	nodes.Each(func(i int, s *goquery.Selection) {
		if rule.Attrs == "text" {
			results = append(results, s.Text())
		} else {
			results = append(results, s.AttrOr(rule.Attrs, ""))
		}
	})

	for _, filter := range rule.Filters {
		results = filter(results)
	}

	return &ParseResult{
		Data: results,
	}, nil
}
