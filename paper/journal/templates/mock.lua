-- mock.lua — make placeholder ("mock") content visibly different in every output.
--
-- Mark text that is NOT real data yet with a span or fenced div of class mock:
--
--     [ค่าจำลอง 12.3 mm]{.mock}
--
--     ::: mock
--     ย่อหน้าทั้งย่อหน้าที่ยังเป็นข้อมูลจำลอง
--     :::
--
-- LaTeX (preview.ps1):  rendered in the colour "mock" defined in preview-header.tex.
-- docx (build.ps1, preview-word.ps1):  bold, with a visible ⟦จำลอง⟧ prefix, since the
--   Word path has no highlight style to lean on.
-- Unlike <mark>, nothing is dropped: the text survives in both outputs, and grepping
-- the drafts for ".mock" / "::: mock" lists everything still to be replaced.

local function is_mock(el)
  return el.classes and el.classes:includes('mock')
end

function Span(el)
  if not is_mock(el) then return nil end
  if FORMAT:match('latex') then
    local out = pandoc.List({pandoc.RawInline('latex', '\\textcolor{mock}{')})
    out:extend(el.content)
    out:insert(pandoc.RawInline('latex', '}'))
    return out
  end
  local out = pandoc.List({pandoc.Str('\u{27E6}\u{0E08}\u{0E33}\u{0E25}\u{0E2D}\u{0E07}\u{27E7} ')})
  out:extend(el.content)
  return pandoc.Strong(out)
end

function Div(el)
  if not is_mock(el) then return nil end
  if FORMAT:match('latex') then
    local out = pandoc.List({pandoc.RawBlock('latex', '\\begingroup\\color{mock}')})
    out:extend(el.content)
    out:insert(pandoc.RawBlock('latex', '\\endgroup'))
    return out
  end
  local out = pandoc.List()
  for _, b in ipairs(el.content) do
    if b.t == 'Para' or b.t == 'Plain' then
      local inl = pandoc.List({pandoc.Str('\u{27E6}\u{0E08}\u{0E33}\u{0E25}\u{0E2D}\u{0E07}\u{27E7} ')})
      inl:extend(b.content)
      out:insert(pandoc.Para({pandoc.Strong(inl)}))
    else
      out:insert(b)
    end
  end
  return out
end
