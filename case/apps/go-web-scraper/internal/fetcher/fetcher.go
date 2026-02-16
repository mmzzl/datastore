package fetcher 

type Fetcher struct {
	clinet *http.Client
	proxyPool *ProxyPool // 代理池
	cookieJar *cookiejar.Jar // Cookie 管理
	userAgent []string // UA 轮换
}

type FetchOptions struct {
	Proxy string // 代理
	Timeout time.Duration // 超时时间
	Headers map[string]string // 请求头
	UserCookie bool 
	RetryPolicy RetryConfig
}
func (f *Fetcher) Fetch(ctx context.Context, url string, opts FetchOptions) (*Response, error) {
	// 构建请求
	req, err := http.NewRequest(opts.Method, url, nil)
	if err != nil {
		return nil, err
	}
	// 设置请求头
	for k, v := range opts.Headers {
		req.Header.Set(k, v)
	}
	// 设置UA
	req.Header.Set("User-Agent", f.userAgent[rand.Intn(len(f.userAgent))])
	// 设置Cookie
	if opts.UserCookie {
		req.Header.Set("Cookie", f.cookieJar.Get(url).String())
	}
	// 设置代理
	if opts.Proxy != "" {
		req.URL.Host = opts.Proxy
	}
	// 发送请求
	resp, err := f.clinet.Do(req)
	if err != nil {
		return nil, err
	}
	// 保存Cookie
	f.cookieJar.SetCookies(url, resp.Cookies())
	return resp, nil
}