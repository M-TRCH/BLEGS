-- journal.lua — the journal's layout rules that pandoc cannot express by itself.
--
-- Applied first in every build (preview.ps1, preview-word.ps1, build.ps1):
--
--   front matter   fenced divs {custom-style="Title" | "Author" | "Affiliation" |
--                  "Corresponding"} map to the styles of the same name in
--                  reference.docx (title 18 pt bold left, author 14, address 12);
--                  for the LaTeX preview the same sizes are applied inline.
--   captions       a paragraph starting "ตารางที่ N" that is followed by an image is
--                  the table caption: 14 pt bold, left, with a blank line above the
--                  caption and below the table.  An image followed by a paragraph
--                  starting "รูปที่ N" is a figure: blank line above the image, the
--                  caption 14 pt bold centred, blank line below it.
--   equations      every display equation is numbered in order of appearance and
--                  set with the number flush right at the column edge: in .docx as
--                  TAB equation TAB (n) in the "Equation" style whose tab stops are
--                  defined in reference.docx, in LaTeX as an amsmath equation
--                  environment.  One blank line above and below.
--
-- The blank lines are real empty paragraphs (<w:p/>) because the styles carry no
-- spacing, which keeps the body text at single spacing everywhere else.

local TABLE = 'ตารางที่'
local FIG = 'รูปที่'
local is_docx = FORMAT:match('docx') ~= nil
local is_latex = FORMAT:match('latex') ~= nil

local function starts(b, prefix)
  if b.t ~= 'Para' and b.t ~= 'Plain' then return false end
  return pandoc.utils.stringify(b):sub(1, #prefix) == prefix
end

local function is_image_para(b)
  if b.t ~= 'Para' and b.t ~= 'Plain' then return false end
  local seen = false
  for _, il in ipairs(b.content) do
    if il.t == 'Image' then seen = true
    elseif il.t ~= 'Space' and il.t ~= 'SoftBreak' then return false end
  end
  return seen
end

local function blank()
  if is_docx then return pandoc.RawBlock('openxml', '<w:p/>') end
  return pandoc.RawBlock('latex', '\\vspace{\\baselineskip}')
end

local function styled(block, style)
  return pandoc.Div({block}, pandoc.Attr('', {}, {['custom-style'] = style}))
end

local function caption(para, style, centred)
  if is_docx then return styled(para, style) end
  if is_latex then
    local inl = pandoc.List({pandoc.RawInline('latex',
      centred and '\\begin{center}\\bfseries ' or '\\noindent\\bfseries ')})
    inl:extend(para.content)
    inl:insert(pandoc.RawInline('latex', centred and '\\end{center}' or '\\par'))
    return pandoc.Para(inl)
  end
  return para
end

local eqn = 0
local function equation(math)
  eqn = eqn + 1
  if is_latex then
    return pandoc.RawBlock('latex', '\\begin{equation}' .. math.text .. '\\end{equation}')
  end
  local tab = pandoc.RawInline('openxml', '<w:r><w:tab/></w:r>')
  local p = pandoc.Para({tab, pandoc.Math('InlineMath', math.text), tab,
                         pandoc.Str('(' .. eqn .. ')')})
  if is_docx then return styled(p, 'Equation') end
  return p
end

local function is_display_math(b)
  return b.t == 'Para' and #b.content == 1 and b.content[1].t == 'Math'
     and b.content[1].mathtype == 'DisplayMath'
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
  local i = 1
  while i <= #blocks do
    local b, nxt = blocks[i], blocks[i + 1]
    if is_display_math(b) then
      out:insert(blank()); out:insert(equation(b.content[1])); out:insert(blank())
    elseif nxt and starts(b, TABLE) and is_image_para(nxt) then
      out:insert(blank()); out:insert(caption(b, 'Table Caption', false))
      out:insert(nxt); out:insert(blank()); i = i + 1
    elseif nxt and is_image_para(b) and starts(nxt, FIG) then
      out:insert(blank()); out:insert(b)
      out:insert(caption(nxt, 'Image Caption', true)); out:insert(blank()); i = i + 1
    else
      out:insert(b)
    end
    i = i + 1
  end
  return out
end

return {
  { Div = front_div },
  { Pandoc = function(doc) doc.blocks = layout(doc.blocks); return doc end },
}
