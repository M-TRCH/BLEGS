-- journal.lua — the journal's layout rules that pandoc cannot express by itself.
--
-- Applied first in every build (preview.ps1, preview-word.ps1, build.ps1).
-- Checked against the journal's own template (kmutnb-article-template.docx) and
-- five published TCI-1 papers on 8 Nov 2026; the matching styles live in
-- reference.docx (see patch-reference-docx.py).
--
--   front matter   fenced divs {custom-style="Title" | "Author" | "Affiliation" |
--                  "Corresponding"} map to the styles of the same name in
--                  reference.docx (title 18 pt bold left, author 14, address 12);
--                  for the LaTeX preview the same sizes are applied inline.
--                  A blank line goes above "คำสำคัญ:" / "Keywords:" as in the template.
--   captions       a paragraph starting "ตารางที่ N" that is followed by an image is
--                  the table caption: left, with a blank line above the caption and
--                  below the table.  An image followed by a paragraph starting
--                  "รูปที่ N" is a figure: blank line above the image, the caption
--                  centred, blank line below it.  Only the label ("ตารางที่ N" /
--                  "รูปที่ N") is bold, the description regular - as in the template.
--   tables         (.docx only) the table image is replaced by the table itself,
--                  read from tables/src/tableN.md - the same source render-tables.py
--                  draws the separate .jpg from - so the manuscript carries native
--                  Word tables (TH Sarabun New 12 pt, full borders; style "Table").
--                  First column left, the rest centred, widths left to Word.
--   equations      every display equation is numbered in order of appearance; in
--                  .docx as "equation TAB (n)" in the "Equation" style: the equation
--                  starts at the paragraph indent and the number sits flush right at
--                  the column edge.  In LaTeX an amsmath equation environment.  One
--                  blank line above and below; consecutive equations share one.
--   headings       a level-2 journal heading (### here) that directly follows a
--                  level-1 heading gets no extra space above it (published papers).
--                  No blank line is added below a table/figure/equation when a
--                  heading follows - the heading's own space above is that line.
--   references     entries after "เอกสารอ้างอิง" get the "Reference" style (hanging
--                  indent) with a tab after "[n]".
--
-- The blank lines are real empty paragraphs (<w:p/>) because the styles carry no
-- spacing, which keeps the body text at single spacing everywhere else.

local TABLE = 'ตารางที่'
local FIG = 'รูปที่'
local REFS = 'เอกสารอ้างอิง'
local is_docx = FORMAT:match('docx') ~= nil
local is_latex = FORMAT:match('latex') ~= nil

local function paper_dir()
  local d = pandoc.path.directory(PANDOC_SCRIPT_FILE)      -- paper/journal/templates
  return pandoc.path.directory(pandoc.path.directory(d))   -- paper
end

local function starts(b, prefix)
  if b.t ~= 'Para' and b.t ~= 'Plain' then return false end
  return pandoc.utils.stringify(b):sub(1, #prefix) == prefix
end

local function image_of(b)
  if b.t ~= 'Para' and b.t ~= 'Plain' then return nil end
  local img = nil
  for _, il in ipairs(b.content) do
    if il.t == 'Image' then img = il
    elseif il.t ~= 'Space' and il.t ~= 'SoftBreak' then return nil end
  end
  return img
end

local function blank()
  if is_docx then return pandoc.RawBlock('openxml', '<w:p/>') end
  return pandoc.RawBlock('latex', '\\vspace{\\baselineskip}')
end

local function styled(block, style)
  return pandoc.Div({block}, pandoc.Attr('', {}, {['custom-style'] = style}))
end

-- bold only "ตารางที่ N" / "รูปที่ N"
local function bold_label(para)
  local c = para.content
  if #c >= 3 and c[1].t == 'Str' and c[2].t == 'Space' and c[3].t == 'Str' then
    local rest = pandoc.List({pandoc.Strong({c[1], c[2], c[3]})})
    for k = 4, #c do rest:insert(c[k]) end
    para.content = rest
  end
  return para
end

local function caption(para, style, centred)
  para = bold_label(para)
  if is_docx then return styled(para, style) end
  if is_latex then
    local inl = pandoc.List({pandoc.RawInline('latex',
      centred and '\\begin{center}' or '\\noindent ')})
    inl:extend(para.content)
    inl:insert(pandoc.RawInline('latex', centred and '\\end{center}' or '\\par'))
    return pandoc.Para(inl)
  end
  return para
end

-- tables/src/tableN.md -> its Table block (docx only)
local function native_table(img)
  local n = img.src:match('table(%d+)%.jpg$')
  if not n or not is_docx then return nil end
  local path = pandoc.path.join({paper_dir(), 'tables', 'src', 'table' .. n .. '.md'})
  local fh = io.open(path, 'rb')
  if not fh then return nil end
  local text = fh:read('a'); fh:close()
  for _, blk in ipairs(pandoc.read(text, 'markdown').blocks) do
    if blk.t == 'Table' then
      for i, spec in ipairs(blk.colspecs) do
        blk.colspecs[i] = {i == 1 and 'AlignLeft' or 'AlignCenter', pandoc.ColWidthDefault}
      end
      -- header row bold (the table style's first-row rule is not applied by Word here)
      for _, row in ipairs(blk.head.rows) do
        for _, cell in ipairs(row.cells) do
          cell.contents = cell.contents:walk({
            Plain = function(p) return pandoc.Plain({pandoc.Strong(p.content)}) end,
            Para = function(p) return pandoc.Para({pandoc.Strong(p.content)}) end,
          })
        end
      end
      return blk
    end
  end
  return nil
end

local eqn = 0
local function equation(math)
  eqn = eqn + 1
  if is_latex then
    return pandoc.RawBlock('latex', '\\begin{equation}' .. math.text .. '\\end{equation}')
  end
  local tab = pandoc.RawInline('openxml', '<w:r><w:tab/></w:r>')
  local p = pandoc.Para({pandoc.Math('InlineMath', math.text), tab,
                         pandoc.Str('(' .. eqn .. ')')})
  if is_docx then return styled(p, 'Equation') end
  return p
end

local function is_display_math(b)
  return b.t == 'Para' and #b.content == 1 and b.content[1].t == 'Math'
     and b.content[1].mathtype == 'DisplayMath'
end

local function xml_escape(s)
  return (s:gsub('&', '&amp;'):gsub('<', '&lt;'):gsub('>', '&gt;'))
end

-- front-matter divs for the LaTeX preview (docx gets them through custom-style)
local function front_div(d)
  local st = d.attributes['custom-style']
  if not st or not is_latex then return nil end
  local out = pandoc.List()
  local flush = '\\setlength{\\parindent}{0pt}'
  if st == 'Title' then
    out:insert(pandoc.RawBlock('latex', '{\\fontsize{18}{22}\\selectfont\\bfseries' .. flush))
    out:extend(d.content); out:insert(pandoc.RawBlock('latex', '\\par}'))
  elseif st == 'Affiliation' or st == 'Corresponding' then
    out:insert(pandoc.RawBlock('latex', (st == 'Corresponding' and '\\vspace{\\baselineskip}' or '') .. '{\\small' .. flush))
    out:extend(d.content); out:insert(pandoc.RawBlock('latex', '\\par}'))
  elseif st == 'Author' then
    out:insert(pandoc.RawBlock('latex', '{' .. flush)); out:extend(d.content)
    out:insert(pandoc.RawBlock('latex', '\\par}'))
  else
    return nil
  end
  return out
end

local function layout(blocks)
  local out = pandoc.List()
  local last_blank = false
  local function push(b) out:insert(b); last_blank = false end
  local function push_blank()
    if not last_blank then out:insert(blank()); last_blank = true end
  end
  -- blank line below an element, unless a heading (which has its own space) follows
  local function blank_unless_heading(nb)
    if nb and nb.t == 'Header' and nb.level <= 3 then return end
    push_blank()
  end
  local in_refs = false
  local prev = nil
  local i = 1
  while i <= #blocks do
    local b, nxt = blocks[i], blocks[i + 1]
    local img_next = nxt and image_of(nxt)
    if is_display_math(b) then
      push_blank(); push(equation(b.content[1])); blank_unless_heading(nxt)
    elseif img_next and starts(b, TABLE) then
      push_blank(); push(caption(b, 'Table Caption', false))
      push(native_table(img_next) or nxt); blank_unless_heading(blocks[i + 2]); i = i + 1
    elseif nxt and image_of(b) and starts(nxt, FIG) then
      push_blank(); push(is_docx and styled(b, 'Captioned Figure') or b)
      push(caption(nxt, 'Image Caption', true)); blank_unless_heading(blocks[i + 2]); i = i + 1
    elseif b.t == 'Header' then
      in_refs = pandoc.utils.stringify(b) == REFS
      if is_docx and b.level == 3 and prev and prev.t == 'Header' and prev.level == 2 then
        push(pandoc.RawBlock('openxml',
          '<w:p><w:pPr><w:pStyle w:val="Heading3"/><w:spacing w:before="0"/></w:pPr>' ..
          '<w:r><w:t xml:space="preserve">' .. xml_escape(pandoc.utils.stringify(b)) ..
          '</w:t></w:r></w:p>'))
      else
        push(b)
      end
    elseif in_refs and is_docx and b.t == 'Para' and #b.content >= 2
           and b.content[1].t == 'Str' and b.content[1].text:match('^%[%d+%]$')
           and b.content[2].t == 'Space' then
      b.content[2] = pandoc.RawInline('openxml', '<w:r><w:tab/></w:r>')
      push(styled(b, 'Reference'))
    elseif (starts(b, 'คำสำคัญ') or starts(b, 'Keywords')) then
      push_blank(); push(b)
    else
      push(b)
    end
    prev = b
    i = i + 1
  end
  return out
end

return {
  { Div = front_div },
  { Pandoc = function(doc) doc.blocks = layout(doc.blocks); return doc end },
}
