/** public/tbbt 下素材的绝对 URL。CSS 自定义属性里的相对 url() 会按样式表位置解析，预览构建（base './'）会错到 assets/ 下，所以统一转成绝对地址 */
export const tbbtUrl = (path: string) => new URL(`${import.meta.env.BASE_URL}tbbt/${path}`, document.baseURI).href;
export const tbbtCssUrl = (path: string) => `url(${tbbtUrl(path)})`;
