import { Link } from "react-router-dom";
import BrandMark from "../components/layout/BrandMark";
import Icon from "../components/ui/Icon";
import { Card } from "../components/ui/kit";

const FEATURES = [
  { icon: "travel_explore", title: "联网检索", desc: "实时搜索与读取网页，报告附带工具痕迹与来源链接。" },
  { icon: "folder_open", title: "知识库", desc: "个人与公共知识库分层管理，文档解析、分块与索引。" },
  { icon: "psychology", title: "研究记忆", desc: "跨会话保存偏好与背景，可随时查看、编辑或删除。" },
  { icon: "extension", title: "Skill 按需加载", desc: "启用的 Skill 注入系统提示，正文由 agent 按需读取。" },
];

/** 首页：品牌主张 + 能力概览 + 入口。 */
export default function Landing() {
  return (
    <section className="flex flex-col gap-section py-section">
      <div className="flex flex-col gap-gutter-md">
        <div className="flex items-center gap-gutter-sm">
          <BrandMark />
          <span className="font-label text-label-sm uppercase tracking-[0.2em] text-light-outline dark:text-dark-outline">Onefold · Research Agent</span>
        </div>
        <h1 className="max-w-2xl font-headline text-[40px] font-semibold leading-tight tracking-tight text-light-on-surface dark:text-dark-on-surface">万般能力，归一入口。</h1>
        <p className="max-w-xl font-body text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant">
          一个云端研究助手：联网检索、知识库问答、Skill 按需加载、研究记忆，把分散的能力收拢到一次对话里。
        </p>
        <div className="flex flex-wrap gap-gutter-sm pt-gutter-sm">
          <Link className="rounded bg-light-primary px-gutter-lg py-2 font-label text-label-md text-light-on-primary transition-opacity hover:opacity-90 dark:bg-dark-primary dark:text-dark-on-primary" to="/chat">开始研究</Link>
          <Link className="rounded border border-light-outline-variant px-gutter-lg py-2 font-label text-label-md text-light-on-surface hover:bg-light-surface-container-high dark:border-dark-outline-variant dark:text-dark-on-surface dark:hover:bg-dark-surface-container-high" to="/documents">知识库</Link>
          <Link className="rounded border border-light-outline-variant px-gutter-lg py-2 font-label text-label-md text-light-on-surface hover:bg-light-surface-container-high dark:border-dark-outline-variant dark:text-dark-on-surface dark:hover:bg-dark-surface-container-high" to="/memory">研究记忆</Link>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-gutter-md sm:grid-cols-2">
        {FEATURES.map((f) => (
          <Card key={f.title} className="flex flex-col gap-gutter-sm p-gutter-lg">
            <Icon name={f.icon} size={22} className="text-light-primary dark:text-dark-primary" />
            <h3 className="font-headline text-title-md text-light-on-surface dark:text-dark-on-surface">{f.title}</h3>
            <p className="font-body text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">{f.desc}</p>
          </Card>
        ))}
      </div>
    </section>
  );
}