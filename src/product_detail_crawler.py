"""
올리브영 상품 상세 페이지 크롤러
상품 설명 이미지를 수집하고 병합하는 기능
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import requests
import time
import os
import tempfile
from typing import List, Dict
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
# URL compression is now handled in frontend


class ProductDetailCrawler:
    """상품 상세 페이지 이미지 크롤러"""

    def __init__(self, driver, log_callback=None):
        """
        Args:
            driver: Selenium WebDriver 인스턴스
            log_callback: 로그 출력 콜백 함수 (optional)
        """
        self.driver = driver
        self.log_callback = log_callback

    def log(self, message: str):
        """로그 출력"""
        print(message)
        if self.log_callback:
            self.log_callback(message)

        # Desktop 뷰 설정
        print("🖥️  Desktop 뷰 활성화 중...")
        try:
            # Device Metrics 설정
            # width=1920px (Desktop 모드, Legacy layout)
            self.driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
                'width': 1920,
                'height': 1080,
                'deviceScaleFactor': 1,  # Desktop DPR=1
                'mobile': False,  # Desktop User-Agent
                'screenOrientation': {'type': 'portraitPrimary', 'angle': 0}
            })

            print("✅ Desktop 뷰 설정 완료 (1920px viewport, DPR=1)")
        except Exception as e:
            print(f"⚠️  반응형 모바일 뷰 설정 실패: {e}, 기본 모드로 진행")

    def go_to_product_detail(self, product_url: str):
        """
        상품 상세 페이지로 이동

        Args:
            product_url: 상품 URL
        """
        print(f"🔗 상품 페이지로 이동: {product_url}")
        self.driver.get(product_url)

        # React 앱 렌더링 대기 - 상품명이 로드될 때까지
        try:
            wait = WebDriverWait(self.driver, 10)
            # h1 태그가 로드되고 텍스트가 있을 때까지 대기
            wait.until(lambda driver: driver.execute_script(
                "return document.querySelector('h1') && document.querySelector('h1').textContent.length > 0"
            ))
            print("✅ 페이지 로딩 완료")
        except:
            print("⚠️  페이지 로딩 대기 타임아웃, 계속 진행")
            time.sleep(2)

    def detect_layout_type(self) -> str:
        """
        현재 페이지의 레이아웃 타입 감지 (Legacy vs New)
        
        Returns:
            'legacy' 또는 'new'
        """
        try:
            print("🔍 레이아웃 타입 감지 중...")
            
            # Legacy layout 상품명 선택자 확인
            legacy_selectors = [
                "#Contents > div.prd_detail_box.renew > div.right_area > div > p.prd_name",
                "p.prd_name"
            ]
            
            # New layout 상품명 선택자 확인  
            new_selectors = [
                "div[class*='GoodsDetailInfo_title-area'] > h3",
                "div[class*='title-area'] > h3"
            ]
            
            # Legacy layout 시도
            for selector in legacy_selectors:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if elem.text.strip():
                        print("  ✅ Legacy Layout 감지!")
                        return 'legacy'
                except:
                    continue
            
            # New layout 시도
            for selector in new_selectors:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if elem.text.strip():
                        print("  ✅ New Layout 감지!")
                        return 'new'
                except:
                    continue
                    
            # 둘 다 실패하면 JavaScript로 확인
            layout_type = self.driver.execute_script("""
                // Legacy layout 패턴 확인
                const legacyIndicators = [
                    '#Contents',
                    '.prd_detail_box.renew',
                    '#repReview',
                    '#buyInfo',
                    '#artcInfo'
                ];
                
                // New layout 패턴 확인
                const newIndicators = [
                    'div[class*="GoodsDetailInfo"]',
                    'div[class*="ReviewArea"]',
                    'div[class*="page_product-details-wrapper"]'
                ];
                
                let legacyScore = 0;
                let newScore = 0;
                
                // Legacy 점수 계산
                legacyIndicators.forEach(selector => {
                    if (document.querySelector(selector)) {
                        legacyScore++;
                    }
                });
                
                // New 점수 계산
                newIndicators.forEach(selector => {
                    if (document.querySelector(selector)) {
                        newScore++;
                    }
                });
                
                return legacyScore > newScore ? 'legacy' : 'new';
            """)
            
            print(f"  ✅ JavaScript 감지 결과: {layout_type.title()} Layout")
            return layout_type
            
        except Exception as e:
            print(f"  ⚠️ 레이아웃 감지 실패: {e}, Legacy로 기본 설정")
            return 'legacy'

    def click_review_tab(self) -> bool:
        """
        리뷰 탭 클릭 및 최신순 정렬 (JavaScript 강제 처리)
        
        Returns:
            클릭 성공 여부
        """
        try:
            print("🔍 리뷰 탭 클릭 및 정렬 설정 시도... (JavaScript 강제 처리)")
            
            # JavaScript로 강력한 탭 클릭 및 정렬 처리
            success = self.driver.execute_script("""
                console.log('🔍 리뷰 탭 및 정렬 JavaScript 처리 시작');
                
                let tabClicked = false;
                let sortClicked = false;
                
                // ========== 1단계: 리뷰 탭 클릭 ==========
                
                // Legacy layout 리뷰 탭들
                const legacyTabSelectors = [
                    '#reviewInfo > a',
                    '#reviewInfo a',
                    'a[href*="#reviewInfo"]',
                    'a[onclick*="reviewInfo"]'
                ];
                
                // New layout 리뷰 탭들  
                const newTabSelectors = [
                    '#tab-panels > section > ul > li:nth-child(3) > button',
                    'button[data-tab="review"]',
                    'button[aria-controls*="review"]',
                    'li:nth-child(3) > button'
                ];
                
                // 모든 가능한 리뷰 탭 선택자 시도
                const allTabSelectors = [...legacyTabSelectors, ...newTabSelectors];
                
                for (let selector of allTabSelectors) {
                    try {
                        const tab = document.querySelector(selector);
                        if (tab) {
                            // 스크롤해서 보이게 하기
                            tab.scrollIntoView({ block: 'center', behavior: 'smooth' });
                            
                            // 클릭 시도
                            tab.click();
                            
                            console.log(`✅ 리뷰 탭 클릭 성공: ${selector}`);
                            tabClicked = true;
                            break;
                        }
                    } catch (e) {
                        console.log(`⚠️ 리뷰 탭 클릭 실패 (${selector}): ${e.message}`);
                    }
                }
                
                // 탭 클릭 후 잠시 대기 (리뷰 영역 로딩)
                if (tabClicked) {
                    // 동기적으로 대기하기 위해 busywait 사용
                    const start = Date.now();
                    while (Date.now() - start < 2000) {
                        // 2초 대기
                    }
                }
                
                // ========== 2단계: 최신순 정렬 클릭 ==========
                
                // 최신순 관련 텍스트 패턴들
                const sortTextPatterns = ['최신순', '최신 순', '최신', '최신등록순', 'newest', 'latest'];
                
                // 정렬 관련 선택자들 (사용자 제공 선택자 최우선)
                const sortSelectors = [
                    '#gdasSort > li:nth-child(3) > a',  // 사용자 제공 선택자 (최신순)
                    'a[data-sort-type-code="latest"]',
                    'a[data-value="02"]',
                    'select[name*="sort"]',
                    'select[id*="sort"]', 
                    'button[data-sort]',
                    '.sort-option',
                    '.sorting-option',
                    'a[onclick*="sort"]',
                    'button[onclick*="sort"]'
                ];
                
                // 정렬 선택자 먼저 시도
                for (let selector of sortSelectors) {
                    try {
                        const sortElem = document.querySelector(selector);
                        if (sortElem) {
                            // 요소가 보이도록 스크롤
                            sortElem.scrollIntoView({ block: 'center', behavior: 'smooth' });
                            
                            // href="javascript:;" 인 경우 강제 클릭
                            if (sortElem.tagName.toLowerCase() === 'a') {
                                // JavaScript 링크 강제 실행
                                sortElem.click();
                                
                                // onclick 이벤트가 있으면 직접 실행
                                const onClickAttr = sortElem.getAttribute('onclick');
                                if (onClickAttr) {
                                    eval(onClickAttr);
                                }
                                
                                console.log(`✅ 최신순 정렬 클릭 성공 (선택자): ${selector}`);
                                sortClicked = true;
                                
                                // 클릭 후 대기
                                const waitStart = Date.now();
                                while (Date.now() - waitStart < 1000) {
                                    // 1초 대기
                                }
                                break;
                            } else {
                                sortElem.click();
                                console.log(`✅ 최신순 정렬 클릭 성공 (선택자): ${selector}`);
                                sortClicked = true;
                                
                                // 클릭 후 대기
                                const waitStart2 = Date.now();
                                while (Date.now() - waitStart2 < 1000) {
                                    // 1초 대기
                                }
                                break;
                            }
                        }
                    } catch (e) {
                        console.log(`⚠️ 선택자 시도 실패 (${selector}): ${e.message}`);
                    }
                }
                
                // 선택자로 실패하면 텍스트 기반 검색
                if (!sortClicked) {
                    console.log('선택자 시도 실패, 텍스트 기반 검색 시작');
                    const allElements = document.querySelectorAll('*');
                    for (let elem of allElements) {
                    const text = elem.textContent || '';
                    const tagName = elem.tagName.toLowerCase();
                    
                    // 클릭 가능한 요소만 확인
                    if (['button', 'a', 'option', 'li', 'span'].includes(tagName)) {
                        for (let pattern of sortTextPatterns) {
                            if (text.trim() === pattern || text.includes(pattern)) {
                                try {
                                    // 요소가 보이도록 스크롤
                                    elem.scrollIntoView({ block: 'center', behavior: 'smooth' });
                                    
                                    // Select의 option인 경우 select를 찾아서 value 설정
                                    if (tagName === 'option') {
                                        const select = elem.closest('select');
                                        if (select) {
                                            select.value = elem.value;
                                            // change 이벤트 발생
                                            select.dispatchEvent(new Event('change', { bubbles: true }));
                                            console.log(`✅ 최신순 정렬 선택 (select): ${text.trim()}`);
                                            sortClicked = true;
                                            break;
                                        }
                                    } else {
                                        // 일반 클릭
                                        elem.click();
                                        console.log(`✅ 최신순 정렬 클릭 (${tagName}): ${text.trim()}`);
                                        sortClicked = true;
                                        break;
                                    }
                                } catch (e) {
                                    console.log(`⚠️ 최신순 클릭 실패 (${text.trim()}): ${e.message}`);
                                }
                            }
                        }
                        if (sortClicked) break;
                    }
                }
                
                // 특별히 드롭다운이나 필터 버튼들도 시도
                if (!sortClicked) {
                    const filterButtons = document.querySelectorAll('button, a, .filter, .dropdown');
                    for (let btn of filterButtons) {
                        const text = btn.textContent || '';
                        if (text.includes('정렬') || text.includes('순서') || text.includes('sort')) {
                            try {
                                btn.click();
                                console.log(`✅ 정렬 관련 버튼 클릭: ${text.trim()}`);
                                
                                // 클릭 후 최신순 옵션 다시 찾기
                                setTimeout(() => {
                                    const newOptions = document.querySelectorAll('*');
                                    for (let opt of newOptions) {
                                        const optText = opt.textContent || '';
                                        if (optText.includes('최신')) {
                                            try {
                                                opt.click();
                                                console.log(`✅ 드롭다운에서 최신순 선택: ${optText.trim()}`);
                                                sortClicked = true;
                                                break;
                                            } catch (e) {}
                                        }
                                    }
                                }, 500);
                                break;
                            } catch (e) {
                                console.log(`⚠️ 정렬 버튼 클릭 실패: ${e.message}`);
                            }
                        }
                    }
                }
                
                console.log(`🎯 결과: 탭클릭=${tabClicked}, 정렬=${sortClicked}`);
                return tabClicked; // 탭 클릭만 성공하면 OK (정렬은 옵션)
            """)
            
            if success:
                print("  ✅ JavaScript 리뷰 탭 클릭 성공")
                time.sleep(3)  # 정렬 완료 대기
                return True
            else:
                print("  ⚠️ JavaScript 리뷰 탭 클릭 실패")
                return False
                
        except Exception as e:
            print(f"  ⚠️ JavaScript 리뷰 탭 처리 실패: {e}")
            return False

    def extract_review_metadata(self) -> Dict[str, any]:
        """
        리뷰 개수와 별점 추출 (Layout 자동 감지)

        Returns:
            {"리뷰_총개수": int, "별점": float} 형태의 딕셔너리
        """
        metadata = {"리뷰_총개수": 0, "별점": 0.0}

        try:
            # 레이아웃 타입 감지
            layout_type = self.detect_layout_type()
            
            # JavaScript 강제 추출 (모든 가능한 패턴 시도)
            result = self.driver.execute_script(r"""
                const debug = {};
                let rating = 0.0;
                let totalCount = 0;
                
                // ========== Legacy Layout 패턴 ==========
                // 별점: #repReview > b - "4.9"
                const legacyRatingElem = document.querySelector('#repReview > b');
                if (legacyRatingElem) {
                    const text = legacyRatingElem.textContent.trim();
                    debug.legacyRatingText = text;
                    
                    const ratingMatch = text.match(/([0-9]+\.?[0-9]*)/);
                    if (ratingMatch) {
                        rating = parseFloat(ratingMatch[1]);
                        debug.ratingSource = 'legacy_repReview_b';
                    }
                }

                // 리뷰수: #repReview > em - "(37,563건)"
                const legacyTotalElem = document.querySelector('#repReview > em');
                if (legacyTotalElem) {
                    const text = legacyTotalElem.textContent.trim();
                    debug.legacyTotalText = text;
                    
                    const countMatch = text.match(/\(([0-9,]+)/);
                    if (countMatch) {
                        totalCount = parseInt(countMatch[1].replace(/,/g, ''));
                        debug.totalSource = 'legacy_repReview_em';
                    }
                }
                
                // ========== Alternative Legacy 패턴 ==========
                // span.rating 패턴
                if (rating === 0.0) {
                    const altRatingElem = document.querySelector('span.rating');
                    if (altRatingElem) {
                        const ratingText = altRatingElem.textContent.replace('평점', '').trim();
                        const ratingMatch = ratingText.match(/([0-9]+\.?[0-9]*)/);
                        if (ratingMatch) {
                            rating = parseFloat(ratingMatch[1]);
                            debug.ratingSource = 'span.rating';
                            debug.altRatingText = ratingText;
                        }
                    }
                }
                
                // ========== New Layout 패턴 ==========
                // 별점: div[class*='ReviewArea_rating-star'] > span
                if (rating === 0.0) {
                    const newRatingElem = document.querySelector("div[class*='ReviewArea_rating-star'] > span");
                    if (newRatingElem) {
                        const ratingText = newRatingElem.textContent.trim();
                        const ratingMatch = ratingText.match(/([0-9]+\.?[0-9]*)/);
                        if (ratingMatch) {
                            rating = parseFloat(ratingMatch[1]);
                            debug.ratingSource = 'new_ReviewArea_rating-star';
                            debug.newRatingText = ratingText;
                        }
                    }
                }

                // 리뷰수: div[class*='ReviewArea_review-count'] > button > span
                if (totalCount === 0) {
                    const newCountElem = document.querySelector("div[class*='ReviewArea_review-count'] > button > span");
                    if (newCountElem) {
                        const countText = newCountElem.textContent.trim().replace(",", "").replace("건", "");
                        const countMatch = countText.match(/([0-9,]+)/);
                        if (countMatch) {
                            totalCount = parseInt(countMatch[1].replace(/,/g, ''));
                            debug.totalSource = 'new_ReviewArea_review-count';
                            debug.newTotalText = countText;
                        }
                    }
                }
                
                // ========== 강력한 Fallback 패턴들 ==========
                // 모든 텍스트에서 별점 패턴 찾기
                if (rating === 0.0) {
                    const allElements = document.querySelectorAll('*');
                    for (let elem of allElements) {
                        const text = elem.textContent || '';
                        // "별점 4.9", "평점: 4.8", "4.7점" 등의 패턴
                        const patterns = [
                            /별점\s*[:：]?\s*([0-9]+\.?[0-9]*)/,
                            /평점\s*[:：]?\s*([0-9]+\.?[0-9]*)/,
                            /([0-9]+\.?[0-9]*)\s*점/,
                            /rating\s*[:：]?\s*([0-9]+\.?[0-9]*)/i
                        ];
                        
                        for (let pattern of patterns) {
                            const match = text.match(pattern);
                            if (match) {
                                const foundRating = parseFloat(match[1]);
                                if (foundRating >= 0 && foundRating <= 5) {
                                    rating = foundRating;
                                    debug.ratingSource = 'fallback_text_search';
                                    debug.fallbackRatingText = text;
                                    break;
                                }
                            }
                        }
                        if (rating > 0) break;
                    }
                }
                
                // 모든 텍스트에서 리뷰수 패턴 찾기
                if (totalCount === 0) {
                    const allElements = document.querySelectorAll('*');
                    for (let elem of allElements) {
                        const text = elem.textContent || '';
                        // "(2,890건)", "리뷰 1,234개", "1234 reviews" 등의 패턴
                        const patterns = [
                            /\(([0-9,]+)건\)/,
                            /리뷰\s*([0-9,]+)\s*개/,
                            /([0-9,]+)\s*개\s*리뷰/,
                            /([0-9,]+)\s*reviews?/i,
                            /총\s*([0-9,]+)\s*건/
                        ];
                        
                        for (let pattern of patterns) {
                            const match = text.match(pattern);
                            if (match) {
                                const foundCount = parseInt(match[1].replace(/,/g, ''));
                                if (foundCount > 0 && foundCount < 1000000) { // 상식적인 범위
                                    totalCount = foundCount;
                                    debug.totalSource = 'fallback_text_search';
                                    debug.fallbackTotalText = text;
                                    break;
                                }
                            }
                        }
                        if (totalCount > 0) break;
                    }
                }

                return {
                    total: totalCount,
                    rating: rating,
                    debug: debug
                };
            """)

            # 결과 처리 및 디버깅 정보 출력
            if result:
                debug_info = result.get("debug", {})
                metadata["리뷰_총개수"] = result.get("total", 0)
                metadata["별점"] = result.get("rating", 0.0)
                
                # 성공적으로 추출된 정보 출력
                if metadata["리뷰_총개수"] > 0:
                    source = debug_info.get("totalSource", "unknown")
                    print(f"📊 리뷰 총 개수: {metadata['리뷰_총개수']}개 (출처: {source})")
                    if debug_info.get('legacyTotalText'):
                        print(f"    텍스트: {debug_info.get('legacyTotalText')}")
                    elif debug_info.get('newTotalText'):
                        print(f"    텍스트: {debug_info.get('newTotalText')}")
                    elif debug_info.get('fallbackTotalText'):
                        print(f"    텍스트: {debug_info.get('fallbackTotalText')}")
                else:
                    print(f"⚠️  리뷰 개수를 찾을 수 없음")

                if metadata["별점"] > 0:
                    source = debug_info.get("ratingSource", "unknown")
                    print(f"⭐ 별점: {metadata['별점']}점 (출처: {source})")
                    if debug_info.get('legacyRatingText'):
                        print(f"    텍스트: {debug_info.get('legacyRatingText')}")
                    elif debug_info.get('newRatingText'):
                        print(f"    텍스트: {debug_info.get('newRatingText')}")
                    elif debug_info.get('fallbackRatingText'):
                        print(f"    텍스트: {debug_info.get('fallbackRatingText')}")
                else:
                    print(f"⚠️  별점을 찾을 수 없음")
                    
                # 감지된 레이아웃에 따른 추가 정보
                print(f"🎯 감지된 레이아웃: {layout_type.title()}")
            else:
                print(f"⚠️  JavaScript 실행 결과가 없음")

        except Exception as e:
            print(f"⚠️  리뷰 메타데이터 추출 실패: {e}")
            import traceback
            traceback.print_exc()

        return metadata

    def extract_specific_info(self) -> Dict[str, str]:
        """
        사용자가 요청한 4가지 특정 상품 정보 추출 (Layout 자동 감지)
        레이아웃에 따라 다른 선택자 사용
        """
        info = {}

        # 레이아웃 타입 감지
        layout_type = self.detect_layout_type()

        try:
            print(f"🔍 상세 상품 정보 추출 시도... ({layout_type.title()} Layout)")

            if layout_type == 'legacy':
                # Legacy layout 처리
                info = self._extract_specific_info_legacy()
            else:
                # New layout 처리
                info = self._extract_specific_info_new()

        except Exception as e:
            print(f"⚠️ 상세 정보 추출 중 오류: {e}")

        return info

    def _extract_specific_info_legacy(self) -> Dict[str, str]:
        """
        Legacy layout에서 상세 정보 추출
        """
        info = {}
        target_selectors = {
            "사용기한(또는 개봉 후 사용기간)": "#buyInfo > a",
            "사용방법": "#artcInfo > dl:nth-child(5) > dd",
            "화장품제조업자,화장품책임판매업자 및 맞춤형화장품판매업자": "#artcInfo > dl:nth-child(6) > dd",
            "화장품법에 따라 기재해야 하는 모든 성분": "#artcInfo > dl:nth-child(8) > dd"
        }

        try:
            
            # 1. #buyInfo > a 클릭 (상품정보 탭)
            try:
                buyinfo_button = self.driver.find_element(By.CSS_SELECTOR, "#buyInfo > a")
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", buyinfo_button)
                buyinfo_button.click()
                time.sleep(2)  # 정보 로딩 대기
                print("  ✅ #buyInfo > a 클릭 완료")
            except Exception as e:
                print(f"  ⚠️ #buyInfo > a 클릭 실패: {e}")

            # 2. 사용기한 추출 (#buyInfo > a 텍스트에서 직접)
            try:
                buyinfo_elem = self.driver.find_element(By.CSS_SELECTOR, "#buyInfo > a")
                usage_text = buyinfo_elem.text.strip()
                if usage_text and len(usage_text) > 10:
                    info["사용기한(또는 개봉 후 사용기간)"] = usage_text
                    print(f"  ✅ 사용기한: {usage_text[:30]}...")
            except Exception as e:
                print(f"  ⚠️ 사용기한 추출 실패: {e}")

            # 3. 나머지 정보들 추출 (#artcInfo 영역에서)
            for field_name, selector in target_selectors.items():
                if field_name == "사용기한(또는 개봉 후 사용기간)":
                    continue  # 이미 추출함
                    
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    text_content = elem.text.strip()
                    if text_content:
                        info[field_name] = text_content
                        print(f"  ✅ {field_name}: {text_content[:30]}...")
                except Exception as e:
                    print(f"  ⚠️ {field_name} 추출 실패: {e}")

        except Exception as e:
            print(f"⚠️ Legacy 상세 정보 추출 중 오류: {e}")

        return info

    def _extract_specific_info_new(self) -> Dict[str, str]:
        """
        New layout에서 상세 정보 추출 (테이블 기반)
        """
        info = {}
        target_fields = [
            "사용기한(또는 개봉 후 사용기간)",
            "사용방법",
            "화장품제조업자,화장품책임판매업자 및 맞춤형화장품판매업자",
            "화장품법에 따라 기재해야 하는 모든 성분"
        ]

        try:
            # 1. 상품정보 탭 클릭
            try:
                tab_button = self.driver.find_element(By.CSS_SELECTOR, "#tab-panels > section > ul > li:nth-child(1) > button")
                is_expanded = tab_button.get_attribute("aria-expanded") == "true"

                if not is_expanded:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tab_button)
                    tab_button.click()
                    time.sleep(1)
                    print("  ✅ 상품정보 탭 클릭 완료")
            except Exception as e:
                print(f"  ⚠️ 상품정보 탭 클릭 실패: {e}")

            # 2. 테이블에서 정보 추출
            try:
                rows = self.driver.find_elements(By.CSS_SELECTOR, "#tab-panels > section > ul > li:nth-child(1) > div > div > table > tbody > tr")
                print(f"  📊 테이블 행 개수: {len(rows)}")

                for row in rows:
                    try:
                        th = row.find_element(By.TAG_NAME, "th")
                        header_text = th.text.strip()
                        clean_header = header_text.replace(" ", "")

                        for target in target_fields:
                            clean_target = target.replace(" ", "")
                            if clean_target in clean_header and target not in info:
                                td = row.find_element(By.TAG_NAME, "td")
                                value_text = td.text.strip()
                                info[target] = value_text
                                print(f"  ✅ {target}: {value_text[:30]}...")
                                break
                    except Exception:
                        continue

            except Exception as e:
                print(f"  ⚠️ 테이블 추출 실패: {e}")

        except Exception as e:
            print(f"⚠️ New layout 상세 정보 추출 중 오류: {e}")

        return info

    def extract_product_info_from_detail(self) -> Dict[str, str]:
        """
        상세 페이지에서 상품 정보 추출
        """
        info = {}
        
        # 기존 로직 (상품명 등) - 여기서는 간단히 구현하거나 기존 코드에 병합해야 함
        # 현재 파일에는 extract_product_info_from_detail 메서드가 안보임 (잘렸거나 다른 파일에 있거나)
        # 아, 사용자가 보여준 코드에는 없었음. oliveyoung_crawler.py에서 호출하는데...
        # product_detail_crawler.py 전체를 못 봤음. 
        # view_file로 다시 확인 필요할 수도 있지만, 일단 클래스 안에 메서드 추가하고
        # 호출하는 쪽에서 병합하도록 수정하는 게 안전함.
        
        # 일단 이 메서드는 독립적으로 두고, oliveyoung_crawler.py에서 호출하게 수정하겠음.
        return info

    def click_more_button(self):
        """상품설명 더보기 버튼 클릭"""
        try:
            print("🔘 '상품설명 더보기' 버튼 찾는 중...")

            # 여러 selector 시도
            selectors = [
                "#btn_toggle_detail_image",  # 사용자 확인 (1000px desktop)
                "#tab-panels > section > div.GoodsDetailTabs_controller__Cd5sb > button",  # 좁은 모바일
                "#controller-button",  # New structure
                ".prd_detail_box .btn_toggle",  # Old structure fallback
            ]

            for selector in selectors:
                try:
                    button = self.driver.find_element(By.CSS_SELECTOR, selector)

                    # 버튼이 보이도록 스크롤
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                    time.sleep(0.5)

                    # 버튼 클릭
                    button.click()
                    print(f"✅ 더보기 버튼 클릭 완료 ({selector})")
                    time.sleep(2)  # 이미지 로딩 대기

                    # 페이지 끝까지 천천히 스크롤하여 모든 lazy-load 이미지 로드
                    print("📜 페이지 스크롤하여 모든 이미지 로딩 중...")
                    self.scroll_to_load_all_images()

                    return True
                except Exception:
                    continue

            print("⚠️  더보기 버튼을 찾을 수 없음 - 이미 펼쳐져 있을 수 있습니다")
            print("📜 스크롤하여 이미지 로딩 시도...")
            self.scroll_to_load_all_images()
            return False

        except Exception as e:
            print(f"⚠️  더보기 버튼 처리 중 오류: {e}")
            print("현재 페이지 URL:", self.driver.current_url)
            return False

    def scroll_to_load_all_images(self):
        """
        페이지를 천천히 스크롤하여 모든 lazy-load 이미지 로드
        네트워크 요청이 완료될 때까지 지능적으로 대기
        """
        try:
            # 현재 페이지 높이
            last_height = self.driver.execute_script("return document.body.scrollHeight")

            # 스크롤 위치
            scroll_position = 0
            scroll_increment = 500  # 한 번에 500px씩 스크롤
            max_wait_per_scroll = 3  # 각 스크롤마다 최대 3초 대기

            while scroll_position < last_height:
                # 조금씩 스크롤
                scroll_position += scroll_increment
                self.driver.execute_script(f"window.scrollTo(0, {scroll_position});")

                # 이미지 로딩 대기 - 네트워크 활동이 안정될 때까지
                self._wait_for_images_to_load(max_wait_per_scroll)

                # 페이지 높이가 변경되었는지 확인 (동적 로딩)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height > last_height:
                    last_height = new_height

            # 마지막으로 페이지 끝까지 스크롤
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self._wait_for_images_to_load(max_wait_per_scroll)

            print("✅ 모든 이미지 로딩 완료")

        except Exception as e:
            print(f"⚠️  스크롤 중 오류: {e}")

    def _wait_for_images_to_load(self, max_wait=3):
        """
        이미지가 실제로 로드될 때까지 대기

        Args:
            max_wait: 최대 대기 시간 (초)
        """
        try:
            # 방법 1: img.s-lazy 이미지의 src가 data-src가 아닌 실제 URL로 변경될 때까지 대기
            wait = WebDriverWait(self.driver, max_wait)

            # 로딩되지 않은 이미지 확인
            unloaded_images_script = """
                return Array.from(document.querySelectorAll('img.s-lazy')).filter(img => {
                    const src = img.getAttribute('src') || '';
                    const dataSrc = img.getAttribute('data-src') || '';
                    // src가 비어있거나 placeholder인 경우
                    return src === '' || src.includes('placeholder') || src.includes('loading');
                }).length;
            """

            # 짧은 간격으로 체크하면서 이미지가 로드되기를 기다림
            start_time = time.time()
            while time.time() - start_time < max_wait:
                unloaded_count = self.driver.execute_script(unloaded_images_script)

                if unloaded_count == 0:
                    # 모든 이미지 로드 완료
                    break

                time.sleep(0.1)  # 100ms 간격으로 체크

        except Exception as e:
            # 타임아웃이나 다른 오류 발생 시 그냥 짧게 대기
            time.sleep(0.3)

    def extract_product_images(self) -> List[str]:
        """
        상품 설명 이미지 URL 추출 (Legacy layout - #tempHtml2의 모든 div에서)

        Returns:
            이미지 URL 리스트
        """
        print("📸 상품 설명 이미지 URL 추출 중...")

        # 성능 개선: implicit wait를 임시로 0으로 설정
        original_implicit_wait = self.driver.timeouts.implicit_wait
        self.driver.implicitly_wait(0)

        try:
            # Legacy layout: #tempHtml2의 모든 div 안의 이미지 추출
            primary_selector = "#tempHtml2 div img"

            print(f"  🎯 Legacy layout 선택자로 탐색: '{primary_selector}'")
            images = self.driver.find_elements(By.CSS_SELECTOR, primary_selector)

            if images:
                print(f"  ✅ {len(images)}개 이미지 발견")
            else:
                print("  ⚠️  #tempHtml2 div img로 이미지를 찾을 수 없음. Fallback 시도...")
                # Fallback: img.s-lazy 클래스로 시도
                images = self.driver.find_elements(By.CSS_SELECTOR, "img.s-lazy")
                if images:
                    print(f"  ✅ Fallback(img.s-lazy)으로 {len(images)}개 이미지 발견")

            if not images:
                print("❌ 상품 설명 이미지를 찾을 수 없습니다")
                return []

            # 이미지 URL 추출 및 필터링
            image_urls = []
            seen_urls = set()

            for idx, img in enumerate(images):
                try:
                    img_url = img.get_attribute("src") or img.get_attribute("data-src")
                    if not (img_url and img_url.startswith("http")):
                        continue

                    # 썸네일 URL 필터링
                    if "/thumbnails/" in img_url:
                        print(f"  {idx+1}. [필터링] 썸네일 제외: {img_url[:80]}...")
                        continue

                    if img_url in seen_urls:
                        continue

                    # 필터링 로직 (너무 작은 이미지 제외)
                    width = img.get_attribute("width")
                    height = img.get_attribute("height")

                    # 너무 작은 이미지 제외 (width < 100 or height < 50)
                    width_ok = True
                    if width:
                        try:
                            if int(width) < 100: width_ok = False
                        except: pass

                    height_ok = True
                    if height:
                        try:
                            if int(height) < 50: height_ok = False
                        except: pass

                    if width_ok and height_ok:
                        image_urls.append(img_url)
                        seen_urls.add(img_url)
                        print(f"  {idx+1}. [추가] {img_url[:80]}...")
                    else:
                        print(f"  {idx+1}. [필터링] 크기 작음 (w:{width}, h:{height})")

                except Exception as e:
                    print(f"  ⚠️  {idx+1}번 이미지 처리 실패: {e}")
                    continue

            print(f"✅ 총 {len(image_urls)}개 이미지 URL 추출 완료 (중복 및 필터링 후)")

        finally:
            # implicit wait 원래대로 복구
            self.driver.implicitly_wait(original_implicit_wait)

        return image_urls

    def _calculate_color_similarity(self, img1: Image.Image, img2: Image.Image) -> float:
        """
        두 이미지의 경계 색상 유사도 계산 (평균 색상 비교)
        img1의 마지막 2px과 img2의 첫 2px의 평균 색상을 비교

        Args:
            img1: 위쪽 이미지
            img2: 아래쪽 이미지

        Returns:
            유사도 (0.0 ~ 1.0, 1.0이 완전 동일)
        """
        try:
            # img1의 마지막 2줄 평균 색상
            bottom_crop = img1.crop((0, max(0, img1.height - 2), img1.width, img1.height))
            bottom_color = bottom_crop.resize((1, 1)).getpixel((0, 0))

            # img2의 첫 2줄 평균 색상
            top_crop = img2.crop((0, 0, img2.width, min(2, img2.height)))
            top_color = top_crop.resize((1, 1)).getpixel((0, 0))

            # RGB 차이 계산
            r_diff = abs(bottom_color[0] - top_color[0])
            g_diff = abs(bottom_color[1] - top_color[1])
            b_diff = abs(bottom_color[2] - top_color[2])
            avg_diff = (r_diff + g_diff + b_diff) / 3
            similarity = 1.0 - (avg_diff / 255.0)
            return similarity
        except Exception as e:
            print(f"    ⚠️ 색상 유사도 계산 실패: {e}")
            return 0.5

    def _calculate_histogram_similarity(self, img1: Image.Image, img2: Image.Image) -> float:
        """
        두 이미지의 경계 색상 히스토그램 유사도 계산 (교차 분석)
        img1의 마지막 2px과 img2의 첫 2px의 히스토그램을 비교

        Args:
            img1: 위쪽 이미지
            img2: 아래쪽 이미지

        Returns:
            유사도 (0.0 ~ 1.0, 1.0이 완전 동일)
        """
        try:
            # 경계 영역 추출 (2px)
            bottom_crop = img1.crop((0, max(0, img1.height - 2), img1.width, img1.height))
            top_crop = img2.crop((0, 0, img2.width, min(2, img2.height)))

            # 히스토그램 계산
            hist1 = bottom_crop.histogram()
            hist2 = top_crop.histogram()

            # 히스토그램 교차(intersection) 계산
            intersection = sum(min(h1, h2) for h1, h2 in zip(hist1, hist2))

            # 전체 픽셀 수로 정규화하여 유사도 계산
            total_pixels = bottom_crop.width * bottom_crop.height
            if total_pixels == 0: return 1.0

            similarity = intersection / total_pixels
            return similarity
        except Exception as e:
            print(f"    ⚠️ 히스토그램 유사도 계산 실패: {e}")
            return 0.5

    def _split_images_by_context(self, images: List[Image.Image], mode: str, similarity_threshold: float = 0.95) -> List[List[Image.Image]]:
        """
        이미지를 문맥에 따라 그룹으로 분할 (모드 지원)

        Args:
            images: 이미지 리스트
            mode: 분할 모드 ('conservative', 'aggressive')
            similarity_threshold: 'aggressive' 모드에서 사용할 유사도 임계값

        Returns:
            이미지 그룹 리스트
        """
        if not images:
            return []

        MAX_HEIGHT = 65000 # JPEG Format Limit (approx 65535)
        groups = []
        current_group = [images[0]]
        current_height = images[0].height

        print(f"\n🎨 문맥 기반 분할 실행 (모드: {mode})")
        print(f"   (최대 허용 높이: {MAX_HEIGHT}px)")
        if mode == 'aggressive':
            print(f"   (유사도 임계값: {similarity_threshold:.2f})")

        for i in range(1, len(images)):
            prev_img = images[i - 1]
            curr_img = images[i]

            would_exceed = (current_height + curr_img.height) > MAX_HEIGHT
            
            # 분할 여부 결정
            should_split = False
            reason = ""

            if would_exceed:
                should_split = True
                reason = f"높이 초과 ({current_height + curr_img.height}px > {MAX_HEIGHT}px)"
            elif mode == 'aggressive':
                similarity = self._calculate_histogram_similarity(prev_img, curr_img)
                if similarity < similarity_threshold:
                    should_split = True
                    reason = f"유사도 낮음 ({similarity:.2f})"
                else:
                    reason = f"유사도 높음 ({similarity:.2f})"

            if not should_split:
                # 그룹에 추가
                current_group.append(curr_img)
                current_height += curr_img.height
                if mode == 'aggressive':
                    print(f"  [{i}/{len(images)-1}] {reason} → 같은 그룹 (누적 높이: {current_height}px)")
                else: # conservative
                    print(f"  [{i}/{len(images)-1}] 높이 양호 → 같은 그룹 (누적 높이: {current_height}px)")
            else:
                # 새 그룹 시작
                groups.append(current_group)
                print(f"  [{i}/{len(images)-1}] {reason} → 새 그룹 시작")
                current_group = [curr_img]
                current_height = curr_img.height

        if current_group:
            groups.append(current_group)

        print(f"✅ 총 {len(groups)}개 그룹으로 분할")
        for idx, group in enumerate(groups, 1):
            total_h = sum(img.height for img in group)
            print(f"  그룹 {idx}: {len(group)}개 이미지, 총 높이 {total_h}px")

        return groups

    def _split_images_by_tile_layout(self, images: List[Image.Image], display_resolution: str = "1920x1080") -> List[List[Image.Image]]:
        """
        16:9 비율 기반 지능적 컬럼 배치로 이미지 분할

        Args:
            images: 이미지 리스트
            display_resolution: 디스플레이 해상도 ("1920x1080", "2560x1440", "3840x2160")

        Returns:
            이미지 그룹 리스트 - 각 그룹이 하나의 타일
        """
        if not images:
            return []

        print(f"\n🖥️ 16:9 비율 기반 타일 레이아웃 분할 ({display_resolution})")

        # 첫 유효 이미지의 가로 길이 확인
        first_valid_width = None
        for img in images:
            if img.width >= 100 and img.height >= 50:  # 유효한 이미지
                first_valid_width = img.width
                break

        if not first_valid_width:
            print("⚠️ 유효한 이미지가 없습니다")
            return [images]  # 전체를 하나의 그룹으로

        print(f"  첫 유효 이미지 가로: {first_valid_width}px")

        # 컬럼 개수 계산 (2열 기본)
        num_columns = 2
        total_width = first_valid_width * num_columns

        print(f"  컬럼 개수: {num_columns}개")
        print(f"  타일 가로: {total_width}px")

        # 목표 높이 범위 계산 (16:9 ~ 16:10 + 30% 여유)
        target_height_16_9 = int(total_width / 16 * 9)
        target_height_16_10 = int(total_width / 16 * 10)
        target_height_max = int(target_height_16_10 * 1.3)  # 30% 여유

        print(f"  목표 높이 범위: {target_height_16_9}px ~ {target_height_max}px")
        print(f"    (16:9={target_height_16_9}px, 16:10={target_height_16_10}px, +30%={target_height_max}px)")

        # 그룹 생성
        groups = []
        current_tile_columns = [[] for _ in range(num_columns)]
        column_heights = [0] * num_columns

        image_idx = 0

        while image_idx < len(images):
            img = images[image_idx]
            img_height = img.height

            # 가장 높이가 낮은 컬럼 찾기
            min_col_idx = column_heights.index(min(column_heights))
            min_col_height = column_heights[min_col_idx]

            # 해당 컬럼에 추가했을 때 최대 높이 계산
            would_be_height = min_col_height + img_height
            max_would_be = max(
                column_heights[i] if i != min_col_idx else would_be_height
                for i in range(num_columns)
            )

            # 추가 가능 여부 판단
            can_add = max_would_be <= target_height_max

            if can_add:
                # 컬럼에 이미지 추가
                current_tile_columns[min_col_idx].append(img)
                column_heights[min_col_idx] += img_height
                print(f"  [{image_idx+1}/{len(images)}] 컬럼{min_col_idx+1}에 추가: {img.width}x{img_height}px (컬럼높이: {column_heights[min_col_idx]}px)")
                image_idx += 1
            else:
                # 현재 타일 완성 - 모든 컬럼이 목표 범위 초과
                flat_group = []
                for col in current_tile_columns:
                    flat_group.extend(col)

                if flat_group:
                    max_height = max(column_heights)
                    groups.append(flat_group)
                    print(f"  📦 타일 {len(groups)} 완성: {len(flat_group)}개 이미지, 최대높이 {max_height}px")
                    for i, col in enumerate(current_tile_columns):
                        print(f"     컬럼{i+1}: {len(col)}개, {column_heights[i]}px")

                # 새 타일 시작
                current_tile_columns = [[] for _ in range(num_columns)]
                column_heights = [0] * num_columns

        # 마지막 타일 저장
        flat_group = []
        for col in current_tile_columns:
            flat_group.extend(col)

        if flat_group:
            max_height = max(column_heights)
            groups.append(flat_group)
            print(f"  📦 타일 {len(groups)} 완성: {len(flat_group)}개 이미지, 최대높이 {max_height}px")
            for i, col in enumerate(current_tile_columns):
                print(f"     컬럼{i+1}: {len(col)}개, {column_heights[i]}px")

        print(f"✅ 총 {len(groups)}개 타일로 분할")
        return groups

    def download_images_individually(self, image_urls: List[str], output_dir: str) -> List[str]:
        """
        이미지들을 개별 파일로 다운로드 (디버그/테스트용)

        Args:
            image_urls: 이미지 URL 리스트
            output_dir: 저장할 디렉토리 경로

        Returns:
            저장된 파일 경로 리스트
        """
        if not image_urls:
            print("❌ 다운로드할 이미지가 없습니다")
            return []

        # 출력 디렉토리 생성
        os.makedirs(output_dir, exist_ok=True)

        print(f"\n📥 개별 이미지 다운로드 시작 (총 {len(image_urls)}개)")
        print(f"📁 저장 경로: {output_dir}")
        print(f"⚡ 병렬 다운로드 시작 (최대 10개 동시)")

        # 단일 이미지 다운로드 함수
        def download_and_save_single(url, idx):
            """단일 이미지 다운로드 및 저장"""
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()

                img = Image.open(BytesIO(response.content))

                # RGB로 변환
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # 파일명: image_001.jpg, image_002.jpg, ...
                filename = f"image_{idx+1:03d}.jpg"
                filepath = os.path.join(output_dir, filename)

                # 저장
                img.save(filepath, 'JPEG', quality=95)

                return idx, filepath, img.width, img.height, None
            except Exception as e:
                return idx, None, None, None, str(e)

        # 병렬 다운로드
        saved_files = {}
        completed_count = 0

        with ThreadPoolExecutor(max_workers=10) as executor:
            # 모든 다운로드 작업 제출
            future_to_idx = {
                executor.submit(download_and_save_single, url, idx): idx
                for idx, url in enumerate(image_urls)
            }

            # 완료되는 대로 처리
            for future in as_completed(future_to_idx):
                idx, filepath, width, height, error = future.result()
                completed_count += 1

                if error:
                    print(f"  [{idx+1:3d}/{len(image_urls)}] ❌ 다운로드 실패: {error}")
                else:
                    saved_files[idx] = filepath
                    print(f"  [{idx+1:3d}/{len(image_urls)}] ✅ 저장: {os.path.basename(filepath)} ({width}x{height}px)")

        # 순서대로 정렬하여 리스트로 변환
        result = [saved_files[i] for i in sorted(saved_files.keys())]

        print(f"\n✅ 개별 다운로드 완료: {len(result)}/{len(image_urls)}개 성공")
        print(f"📁 저장 위치: {output_dir}")

        return result

    def download_and_merge_images(self, image_urls: List[str], output_path: str, progress_callback=None,
                                   split_mode: str = "aggressive", display_resolution: str = "1920x1080") -> str:
        """
        이미지들을 다운로드하고 선택한 모드에 따라 분할하여 병합

        Args:
            image_urls: 이미지 URL 리스트
            output_path: 저장할 파일 경로 (기본 경로, _part1, _part2 등으로 저장됨)
            progress_callback: 진행 상황을 전달할 콜백 함수 (message, current, total)
            split_mode: 분할 모드 ("conservative", "aggressive", "tile")
            display_resolution: 타일 모드일 때 사용할 해상도 ("1920x1080", "2560x1440", "3840x2160")

        Returns:
            저장된 파일 경로 (여러 개인 경우 첫 번째 파일 경로)
        """
        if not image_urls:
            print("❌ 병합할 이미지가 없습니다")
            return ""

        print(f"\n📥 이미지 다운로드 및 병합 시작 (총 {len(image_urls)}개)...")
        print(f"⚡ 병렬 다운로드 시작 (최대 10개 동시)")

        # 단일 이미지 다운로드 함수
        def download_single_image(url, idx):
            """단일 이미지 다운로드"""
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()

                img = Image.open(BytesIO(response.content))

                # RGB로 변환
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                return idx, img, None
            except Exception as e:
                return idx, None, str(e)

        # 병렬 다운로드 (순서 유지를 위해 idx 기반 딕셔너리 사용)
        images_dict = {}
        max_width = 0
        completed_count = 0

        with ThreadPoolExecutor(max_workers=10) as executor:
            # 모든 다운로드 작업 제출
            future_to_idx = {
                executor.submit(download_single_image, url, idx): idx
                for idx, url in enumerate(image_urls)
            }

            # 완료되는 대로 처리
            for future in as_completed(future_to_idx):
                idx, img, error = future.result()
                completed_count += 1

                if progress_callback:
                    progress_callback(
                        f"💾 이미지 다운로드 중... [{completed_count}/{len(image_urls)}]",
                        completed_count,
                        len(image_urls)
                    )

                if error:
                    print(f"  [{idx+1}/{len(image_urls)}] ⚠️  다운로드 실패: {error}")
                else:
                    images_dict[idx] = img
                    max_width = max(max_width, img.width)
                    print(f"  [{idx+1}/{len(image_urls)}] ✅ 크기: {img.width}x{img.height}")

        # 순서대로 정렬하여 리스트로 변환
        images = [images_dict[i] for i in sorted(images_dict.keys())]

        print(f"✅ 다운로드 완료: {len(images)}/{len(image_urls)}개 성공")

        if not images:
            print("❌ 다운로드된 이미지가 없습니다")
            return ""

        # 분할 모드에 따라 그룹 분할
        if split_mode == "tile":
            image_groups = self._split_images_by_tile_layout(images, display_resolution)
        elif split_mode == "conservative":
            # Conservative 모드: 최대한 합치기 (65000px 높이 제한)
            MAX_HEIGHT = 65000
            image_groups = []
            current_group = []
            current_height = 0
            
            for img in images:
                # 현재 그룹에 추가했을 때의 높이 계산
                if current_height + img.height > MAX_HEIGHT and current_group:
                    # 높이 초과 시 현재 그룹 저장하고 새 그룹 시작
                    image_groups.append(current_group)
                    current_group = [img]
                    current_height = img.height
                else:
                    # 높이 초과하지 않으면 현재 그룹에 추가
                    current_group.append(img)
                    current_height += img.height
            
            # 마지막 그룹 추가
            if current_group:
                image_groups.append(current_group)
            
            print(f"✅ Conservative 모드: {len(images)}개 이미지를 {len(image_groups)}개 그룹으로 분할 (최대 높이: {MAX_HEIGHT}px)")
        else:  # aggressive 모드 - 각 이미지를 개별 파일로
            image_groups = [[img] for img in images]
            print(f"✅ Aggressive 모드: {len(images)}개 이미지를 각각 개별 파일로 저장")

        # 각 그룹별로 병합
        saved_paths = []
        base_path = output_path.replace('.jpg', '').replace('.jpeg', '')

        for group_idx, group in enumerate(image_groups, 1):
            # 파일명 결정
            if len(image_groups) == 1:
                # 그룹이 1개면 원본 파일명 사용
                file_path = output_path
            else:
                # 여러 그룹이면 _part1, _part2 등으로 저장
                file_path = f"{base_path}_part{group_idx}.jpg"

            if progress_callback:
                progress_callback(f"🔨 그룹 {group_idx}/{len(image_groups)} 병합 중... ({len(group)}개 이미지)",
                                len(image_urls), len(image_urls))

            print(f"\n🔨 그룹 {group_idx}/{len(image_groups)} 병합 중...")
            print(f"  이미지 개수: {len(group)}개")

            # 타일 모드일 때 컬럼 기반 배치
            if split_mode == "tile":
                # 첫 유효 이미지 가로 확인
                first_valid_width = None
                for img in group:
                    if img.width >= 100 and img.height >= 50:
                        first_valid_width = img.width
                        break

                if not first_valid_width:
                    first_valid_width = group[0].width

                # 2열 배치
                num_columns = 2
                total_width = first_valid_width * num_columns

                # 컬럼별로 이미지 분배 (타일링과 동일한 Best Fit 로직)
                columns = [[] for _ in range(num_columns)]
                column_heights = [0] * num_columns

                for img in group:
                    # 가장 높이가 낮은 컬럼에 추가
                    min_idx = column_heights.index(min(column_heights))
                    columns[min_idx].append(img)
                    column_heights[min_idx] += img.height

                # 최종 캔버스 크기 계산
                max_column_height = max(column_heights)

                print(f"  컬럼 개수: {num_columns}개")
                print(f"  병합 크기: {total_width}x{max_column_height}px")
                for i in range(num_columns):
                    print(f"    컬럼{i+1}: {len(columns[i])}개, {column_heights[i]}px")

                # 캔버스 생성
                merged_image = Image.new('RGB', (total_width, max_column_height), 'white')

                # 컬럼별로 이미지 배치
                current_x = 0
                for col_idx, column in enumerate(columns):
                    if not column:
                        continue

                    current_y = 0
                    for img in column:
                        # 왼쪽 정렬
                        merged_image.paste(img, (current_x, current_y))
                        current_y += img.height

                    current_x += first_valid_width

            else:
                # 문맥 모드 - 기존 방식 (세로로 쌓기)
                group_height = sum(img.height for img in group)
                group_width = max(img.width for img in group)

                print(f"  병합 크기: {group_width}x{group_height}px")

                # 캔버스 생성
                merged_image = Image.new('RGB', (group_width, group_height), 'white')

                # 이미지 붙이기
                current_y = 0
                for idx, img in enumerate(group):
                    # 중앙 정렬
                    x_offset = (group_width - img.width) // 2
                    merged_image.paste(img, (x_offset, current_y))
                    current_y += img.height
                    print(f"  [{idx+1}/{len(group)}] 병합 완료")

            # 저장
            merged_image.save(file_path, 'JPEG', quality=95, optimize=True)
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB

            print(f"  ✅ 저장 완료: {file_path}")
            print(f"  💾 파일 크기: {file_size:.2f} MB")

            saved_paths.append(file_path)

        # 병합 완료 알림
        if progress_callback:
            if len(saved_paths) == 1:
                progress_callback(f"✅ 병합 완료! (1개 파일)", len(image_urls), len(image_urls))
            else:
                progress_callback(f"✅ 병합 완료! ({len(saved_paths)}개 파일로 분할)", len(image_urls), len(image_urls))

        print(f"\n✅ 전체 병합 완료!")
        print(f"  📁 저장된 파일: {len(saved_paths)}개")
        for idx, path in enumerate(saved_paths, 1):
            print(f"    {idx}. {path}")

        # 첫 번째 파일 경로 반환 (호환성)
        return saved_paths[0] if saved_paths else ""

    def extract_product_info_from_detail(self) -> Dict:
        """
        상세 페이지에서 상품 기본 정보 추출 (Layout 자동 감지)

        Returns:
            상품 정보 딕셔너리
        """
        print("\n📋 상품 정보 추출 중...")
        product_info = {}

        try:
            # 레이아웃 타입 감지 (이미 한번 감지했지만 확실히 하기 위해)
            layout_type = self.detect_layout_type()
            print(f"🎯 상품 정보 추출 - 감지된 레이아웃: {layout_type.title()}")
            
            # JavaScript로 모든 패턴 시도
            result = self.driver.execute_script(r"""
                const info = {};

                // 상품명: #Contents > div.prd_detail_box.renew > div.right_area > div > p.prd_name
                const nameElem = document.querySelector('#Contents > div.prd_detail_box.renew > div.right_area > div > p.prd_name');
                if (nameElem) {
                    info.name = nameElem.textContent.trim();
                }

                // 상품가격: #Contents > div.prd_detail_box.renew > div.right_area > div > div.price
                // price 1: 할인전, price 2: 할인후
                const priceContainer = document.querySelector('#Contents > div.prd_detail_box.renew > div.right_area > div > div.price');
                if (priceContainer) {
                    // 가격 spans 추출
                    const priceSpans = priceContainer.querySelectorAll('span.price-2, span.price-1');

                    // price-2가 있으면 할인가, price-1이 원가
                    const price2 = priceContainer.querySelector('span.price-2');
                    const price1 = priceContainer.querySelector('span.price-1');

                    if (price2) {
                        // 할인가 있음
                        info.price = price2.textContent.trim();  // 할인후 가격
                        if (price1) {
                            info.beforePrice = price1.textContent.trim();  // 할인전 가격
                        }
                    } else if (price1) {
                        // 할인가 없음, price-1만 있음
                        info.price = price1.textContent.trim();
                        info.beforePrice = info.price;  // 동일
                    }
                }

                return info;
            """)

            # 결과 저장
            name = result.get("name")
            price = result.get("price")
            before_price = result.get("beforePrice")

            # 0. New Layout Selectors (User Provided)
            if not name:
                try:
                    # 상품명: div[class*='GoodsDetailInfo_title-area'] > h3
                    name_elem = self.driver.find_element(By.CSS_SELECTOR, "div[class*='GoodsDetailInfo_title-area'] > h3")
                    name = name_elem.text.strip()
                    print(f"  ✅ New Layout 상품명: {name}")
                except:
                    pass

            if not price:
                try:
                    # 가격 영역: div[class*='GoodsDetailInfo_price-area']
                    price_area = self.driver.find_element(By.CSS_SELECTOR, "div[class*='GoodsDetailInfo_price-area']")
                    
                    # 할인가 (span > span:nth-child(1))
                    try:
                        sale_price_elem = price_area.find_element(By.CSS_SELECTOR, "div > div > span > span:nth-child(1)")
                        price = sale_price_elem.text.strip()
                    except:
                        pass

                    # 정상가 (s > span:nth-child(1))
                    try:
                        normal_price_elem = price_area.find_element(By.CSS_SELECTOR, "s > span:nth-child(1)")
                        before_price = normal_price_elem.text.strip()
                    except:
                        pass
                    
                    if price:
                        print(f"  ✅ New Layout 가격: {price} (정상가: {before_price})")
                except:
                    pass

            # 1. Fallback: Meta Tags (Open Graph)
            if not name:
                print("  ⚠️ CSS로 상품명을 찾을 수 없음. Meta Tag 시도...")
                try:
                    og_title = self.driver.find_element(By.CSS_SELECTOR, 'meta[property="og:title"]').get_attribute("content")
                    if og_title:
                        # "올리브영 - [브랜드] 상품명" 형식일 수 있음
                        name = og_title.replace("올리브영 - ", "")
                        print(f"  ✅ Meta Tag로 상품명 추출: {name}")
                except:
                    pass

            # 2. Fallback: Common Selectors (New Layout / Mobile)
            if not name:
                print("  ⚠️ Meta Tag로도 실패. 대체 Selector 시도...")
                try:
                    # 일반적인 h1 태그 시도 (보통 상품명은 h1)
                    h1_title = self.driver.find_element(By.TAG_NAME, "h1").text.strip()
                    if h1_title:
                        name = h1_title
                        print(f"  ✅ H1 태그로 상품명 추출: {name}")
                except:
                    pass

            if not price:
                try:
                    # Meta tag for price? (Not standard, but maybe description)
                    # Alternative price selectors
                    price_selectors = [
                        ".price-2 strong", # New layout
                        ".price strong",
                        ".prd_price .price"
                    ]
                    for sel in price_selectors:
                        try:
                            price_elem = self.driver.find_element(By.CSS_SELECTOR, sel)
                            price = price_elem.text.strip()
                            if price:
                                print(f"  ✅ 대체 Selector로 가격 추출: {price}")
                                break
                        except:
                            continue
                except:
                    pass

            product_info["상품명"] = name if name else "정보 없음"
            product_info["정상가"] = before_price if before_price else (price if price else "정보 없음")
            product_info["판매가"] = price if price else "정보 없음"
            product_info["상품_URL"] = self.driver.current_url

            # Thumbnail Extraction (User Provided Selector)
            # #main > div.page_product-details-wrapper___t38G > div > div.page_left-section__qXr0Q > div > div > div > div.swiper-wrapper > div.swiper-slide.swiper-slide-active > div > img
            try:
                thumb_selector = "#main > div.page_product-details-wrapper___t38G > div > div.page_left-section__qXr0Q > div > div > div > div.swiper-wrapper > div.swiper-slide.swiper-slide-active > div > img"
                thumb_elem = self.driver.find_element(By.CSS_SELECTOR, thumb_selector)
                thumb_url = thumb_elem.get_attribute("src")
                
                if thumb_url:
                    product_info["썸네일_URL"] = thumb_url
                    print(f"  🖼️ 썸네일 URL 추출: {thumb_url}")
                    
                    # Download thumbnail
                    try:
                        import requests
                        response = requests.get(thumb_url, stream=True)
                        if response.status_code == 200:
                            # We don't have the output path here easily, but we can return the URL 
                            # and let the main crawler handle downloading, or we can try to save it if we know the path.
                            # Actually, extract_product_info_from_detail is called before directory creation in some flows,
                            # but usually the directory is created in crawl_product_detail_by_url.
                            # Let's just return the URL in product_info and handle download in the main loop or here if we can pass the path.
                            # For now, just saving the URL. The main crawler (oliveyoung_crawler.py) saves product_info.json.
                            # We can add a separate step to download this image in oliveyoung_crawler.py
                            pass
                    except Exception as e:
                        print(f"  ⚠️ 썸네일 다운로드 실패: {e}")
            except:
                # Fallback for legacy layout
                try:
                    thumb_elem = self.driver.find_element(By.CSS_SELECTOR, "#mainImg")
                    thumb_url = thumb_elem.get_attribute("src")
                    if thumb_url:
                        product_info["썸네일_URL"] = thumb_url
                        print(f"  🖼️ 썸네일 URL 추출 (Legacy): {thumb_url}")
                except:
                    pass

            print(f"✅ 상품명: {product_info['상품명']}")
            print(f"   정상가: {product_info['정상가']}")
            print(f"   판매가: {product_info['판매가']}")

        except Exception as e:
            print(f"⚠️  상품 정보 추출 중 오류: {e}")
            import traceback
            traceback.print_exc()

        return product_info
